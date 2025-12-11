import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import os
import sys

try:
    from generate_graph import load_profiles, normalize_percent, compute_similarity, build_graph, detect_communities, describe_community
except ImportError:
    print("ERRO: Não foi possível importar as funções do 'generate_graph.py'.")
    print("Certifique-se de que o arquivo existe e as funções estão definidas.")
    sys.exit(1)

# Adicione esta função logo após o bloco de imports

def standardize_manga_source(raw_source: str) -> str:
    """
    Normaliza a string de source/tipo para ser comparável com a dos animes.
    """
    if not raw_source:
        return "Other"
    
    s = raw_source.strip().lower()
    
    # Light Novel/Novel
    if "light novel" in s or "Novel" in s or "novel" in s:
        return "Light Novel"
    
    # Manhwa / Manhua / Webcomic
    if "manhwa" in s or "Manhua" in s or "manhua" in s:
        return "Manhwa"
        
    # Manga
    if "manga" in s:
        return "Manga"
        
    # Original (não existe, pode ser usado para uma checagem futura)
    if "original" in s:
        return "Original"
        
    # 5. Outros
    return "Other"

# --- 1. CONSTANTES (Devido à estrutura do profiles.csv) ---

# Gêneros e Sources usados no seu profiles.csv
# Esses são os rótulos internos que definem a estrutura do seu vetor de features.
SOURCES_ALVO = ["Manga", "Light_Novel", "Original", "Manhwa", "Other"]
GENEROS_ALVO = [
    "Action", "Adventure", "Comedy", "Drama", 
    "Fantasy", "Sci-Fi", "Slice_of_Life", "Romance", 
    "Supernatural", "Suspense", "Sports"
]

ALL_FEATURES = (
    [f"Source_{s}" for s in SOURCES_ALVO] + 
    [f"Genre_{g}" for g in GENEROS_ALVO]
)

def load_manga_data(path: str) -> pd.DataFrame:
    """Carrega o CSV de mangás."""
    try:
        df = pd.read_csv(path)
        df['id'] = df['id'].astype(str) 
        df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(1.0) # Trata NaN, desnecessário quando não há mídia adulta na base de dados.
        # Garante que a coluna 'generos' e 'tipo' não são None
        df['generos'] = df['generos'].fillna('')
        df['tipo'] = df['tipo'].fillna('Other')
        return df
    except FileNotFoundError:
        print(f"ERRO: Arquivo de mangás não encontrado em {path}.")
        return pd.DataFrame()

def create_manga_vectors(manga_df: pd.DataFrame, all_features: List[str]) -> pd.DataFrame:
    """
    Converte os dados de mangás (gêneros e tipo) em um vetor de features.
    Usa o 'score' do mangá como peso.
    Aplica Normalização L1 para consistência com os perfis L1-normalizados.
    """
    
    # Cria o DataFrame vetorizado inicial, com IDs como índice
    manga_vectors = pd.DataFrame(index=manga_df['id'], columns=all_features).fillna(0.0)
    
    for _, row in manga_df.iterrows():
            manga_id = row['id']
            score_weight = row['score'] / 10.0

            standard_source_key = standardize_manga_source(str(row['tipo']))
            
            # Cria a coluna Feature, substituindo o espaço por underscore
            source = standard_source_key.replace(' ', '_')
            source_col = f"Source_{source}"

            # Verifica se a coluna padronizada existe antes de usar
            if source_col in manga_vectors.columns:
                manga_vectors.loc[manga_id, source_col] = score_weight
            
            # Processa o campo 'generos'
            genres = [g.strip().replace(' ', '_') for g in str(row['generos']).split(',') if g.strip()]
            for genre in genres:
                genre_col = f"Genre_{genre}"
                if genre_col in manga_vectors.columns:
                    manga_vectors.loc[manga_id, genre_col] = score_weight

    # Normalização L1
    manga_vectors_norm = manga_vectors.div(manga_vectors.sum(axis=1), axis=0).fillna(0.0)

    print(f" Vetorização de {len(manga_vectors_norm)} mangás concluída.")
    return manga_vectors_norm.astype(float)

def calculate_community_vector(df_norm_profiles: pd.DataFrame, community_users: List[str]) -> pd.Series:
    """
    Calcula o vetor de preferência médio para uma comunidade de usuários.
    Usa o DF de perfis L1-normalizado (df_norm).
    """
    if not community_users:
        return pd.Series(0, index=df_norm_profiles.columns)
        
    # Retorna a média das linhas dos usuários na comunidade
    community_vector = df_norm_profiles.loc[community_users].mean(axis=0)
    return community_vector

def recommend_manga_for_community(community_vector: pd.Series, manga_vectors: pd.DataFrame) -> pd.Series:
    """
    Calcula a similaridade de cosseno entre o vetor da comunidade e todos os mangás
    e retorna os mangás ordenados pela similaridade.
    """

    manga_vectors_aligned = manga_vectors[community_vector.index] 
    
    community_array = community_vector.values.reshape(1, -1)
    manga_array = manga_vectors_aligned.values
    
    # Calcular a similaridade de cosseno
    sim_scores = cosine_similarity(community_array, manga_array)
    
    sim_series = pd.Series(
        sim_scores.flatten(), 
        index=manga_vectors_aligned.index, 
        name='similarity_score'
    )
    
    # Retorna os mangás mais similares ordenados
    return sim_series.sort_values(ascending=False)

def main_recommender(
    profiles_path: str = 'profiles.csv', 
    mangas_path: str = 'mangas_dados_essenciais.csv',
    threshold: float = 0.98,
    num_recommendations: int = 5
):
    """
    Orquestra o processo de clusterização e recomendação.
    """
    
    # Clusterização de Perfis
    print("\n--- Clusterização de Perfis ---")
    
    # Carrega o DF original (necessário para describe_community)
    df_raw = load_profiles(profiles_path)
    # Normaliza L1 (necessário para calculate_community_vector)
    df_norm = normalize_percent(df_raw) 
    
    print("Calculando similaridade e construindo grafo...")
    sim_df = compute_similarity(df_norm)
    G = build_graph(sim_df, threshold)
    
    print("Detectando comunidades...")
    comms = detect_communities(G) # Usa detect_communities do graph_creator.py
    
    if not comms:
        print("Não foi detectada nenhuma comunidade. Tente reduzir o THRESHOLD.")
        return
        
    print(f"Grafo: {len(G.nodes)} nós. Encontradas {len(comms)} comunidades.")

    # Importa a função geradora de nomes
    from generate_graph import draw_graph, generate_community_names

    # gera nomes
    community_names = generate_community_names(df_raw, comms, top_k=2)

    # desenha grafo com os nomes
    draw_graph(G, comms, df_raw, community_names=community_names, output="graph_comm.png")

    # Carrega o csv de mangás para adaptação
    print("\n--- Preparação dos Mangás para Recomendação ---")
    manga_data_raw = load_manga_data(mangas_path)
    if manga_data_raw.empty:
        return
        
    manga_vectors = create_manga_vectors(manga_data_raw, ALL_FEATURES)
    
    # --- Recomendação por Comunidade e Escrita no arquivo de saída ---
    print("\n--- Recomendação por Comunidade ---")

    # Cria um Arquivo de saída
    output_path = "output.dat"
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write("=== RESULTADO DA CLUSTERIZAÇÃO E RECOMENDAÇÃO ===\n\n")
        f_out.write(f"Total de comunidades: {len(comms)}\n\n")

    print("\n--- Recomendação por Comunidade ---")

    # Abre o arquivo em modo append para registrar as recomendações
    with open(output_path, "a", encoding="utf-8") as f_out:
        for i, community_users in enumerate(comms):
            if not community_users:
                continue

            # Calcula o Vetor de Preferência da Comunidade
            community_vector = calculate_community_vector(df_norm, community_users)

            # Caracteriza a Comunidade
            details = describe_community(df_raw, community_users)

            # --- Impressão normal ---
            print(f"\n[COMUNIDADE {i+1}] ({details['n_users']} usuários)")
            print(f"  > Foco Principal: Origem - {details['source']}. "
                  f"Gêneros - {', '.join(details['genres'])}")

            # --- Registro no arquivo ---
            f_out.write(f"[COMUNIDADE {i+1}] ({details['n_users']} usuários)\n")
            f_out.write(f"  Foco Principal: Origem - {details['source']}. "
                        f"Gêneros - {', '.join(details['genres'])}\n")

            # Recomenda mangás
            sim_results = recommend_manga_for_community(community_vector, manga_vectors)
            top_n = sim_results.head(num_recommendations)

            print(f"  --- Top {num_recommendations} Mangás Não Adaptados Recomendados ---")
            f_out.write(f"  --- Top {num_recommendations} Mangás Não Adaptados Recomendados ---\n")

            for manga_id, score in top_n.items():
                manga_info = manga_data_raw[manga_data_raw['id'] == manga_id].iloc[0]

                # Impressão na tela
                print(f"  [{score:.4f}] {manga_info['nome']}")
                print(f"    - Score MAL: {manga_info['score']:.2f} | "
                      f"Tipo: {manga_info['tipo']} | Gêneros: {manga_info['generos']}")

                # Salvamento no arquivo
                f_out.write(f"  [{score:.4f}] {manga_info['nome']}\n")
                f_out.write(f"    - Score MAL: {manga_info['score']:.2f} | "
                            f"Tipo: {manga_info['tipo']} | Gêneros: {manga_info['generos']}\n")

            f_out.write("\n")  # espaço entre comunidades

# --- EXECUÇÃO ---

if __name__ == "__main__":
    # Caminhos dos arquivos de entrada e saída
    FILE_PROFILES = "profiles.csv"
    FILE_MANGAS = "mangas_cache.csv"

    # Valores do threshold e número de recomendações geradas.
    THRESHOLD = 0.98 
    NUM_RECS = 5
    
    if os.path.exists(FILE_PROFILES) and os.path.exists(FILE_MANGAS):
        main_recommender(FILE_PROFILES, FILE_MANGAS, THRESHOLD, NUM_RECS)
    else:
        print(f"\nErro: Arquivos de dados ('{FILE_PROFILES}' ou '{FILE_MANGAS}') não encontrados. Verifique os caminhos.")