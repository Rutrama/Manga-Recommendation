import csv
import time
from tqdm import tqdm # Importamos tqdm para ter uma barra de progresso visual
import os

# Importando as funções dos seus respectivos módulos
from extract_users import extrair_pagina_usuarios
from extract_anime import load_anime_cache, initialize_cache_file
from normalizer import create_user_profile

# --- CONFIGURAÇÕES GLOBAIS ---

# Definição das categorias para o vetor de perfil
SOURCES_ALVO = [
    "Manga", "Light Novel", "Original", "Manhwa", "Other"
]

GENEROS_ALVO = [
    "Action", "Adventure", "Comedy", "Drama", 
    "Fantasy", "Sci-Fi", "Slice of Life", "Romance", 
    "Supernatural", "Suspense", "Sports"
]

# Definição dos nomes dos arquivos
USUARIOS_INPUT_FILE = "usernames.csv"
ANIME_CACHE_FILE = "animes_cache.csv"
PROFILES_OUTPUT_FILE = "profiles.csv"

# Estrutura do arquivo profiles.csv
PROFILE_FIELDNAMES = ["username"] + \
                     [f"Source_{s.replace(' ', '_')}" for s in SOURCES_ALVO] + \
                     [f"Genre_{g.replace(' ', '_')}" for g in GENEROS_ALVO]

# Limites para a execução (teste)
USUARIOS_LIMITE_PAGINAS = 5
PROFILES_LIMITE = 1000

def run_pipeline():
    print("--- EXTRAÇÃO DE USUÁRIOS ATIVOS ---")
    
    # 1.1 Extrair usuários (ou carregar de arquivo, se existir)
    active_users = []
    try:
        if not os.path.exists(USUARIOS_INPUT_FILE):
             # Se o arquivo não existe, executa o scraper de usuários
            time.sleep(50)
            active_users = extrair_pagina_usuarios(limit_pages=USUARIOS_LIMITE_PAGINAS)
            with open(USUARIOS_INPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["username"])
                writer.writerows([[u] for u in active_users])
        else:
            # Se o arquivo existe, carrega
            with open(USUARIOS_INPUT_FILE, mode="r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader) # Pula cabeçalho
                active_users = [row[0] for row in reader if row]
            print(f"Usuários carregados de {USUARIOS_INPUT_FILE}: {len(active_users)}")

    except Exception as e:
        print(f"Erro na extração/carregamento de usuários: {e}")
        return

    # Limita o processamento de perfis para testes
    users_to_process = active_users[:PROFILES_LIMITE]
    if not users_to_process:
        print("Nenhum usuário para processar. Encerrando.")
        return

    print(f"Total de usuários a serem processados: {len(users_to_process)}")
    print("\n--- INICIALIZAÇÃO E CARREGAMENTO DE CACHE ---")

    # 2.1 Inicializa o arquivo de cache de animes
    initialize_cache_file()
    
    # 2.2 Carrega o cache de animes em memória
    anime_cache = load_anime_cache(ANIME_CACHE_FILE)
    
    print("\n Geração do perfis e incrementação do cache")

    # Abre o arquivo de perfis
    with open(PROFILES_OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as profile_csv:
        writer_profile = csv.DictWriter(profile_csv, fieldnames=PROFILE_FIELDNAMES)
        writer_profile.writeheader()
        
        # O processamento do cache é feito dentro do loop de perfis
        with open(ANIME_CACHE_FILE, mode="a", newline="", encoding="utf-8") as cache_append_f:
            writer_cache = csv.writer(cache_append_f)

            # Itera sobre os usuários
            for username in tqdm(users_to_process, desc="Processando Perfis"):
                time.sleep(1)
                user_vector = create_user_profile(
                    username, 
                    anime_cache, 
                    SOURCES_ALVO, 
                    GENEROS_ALVO,
                    writer_cache # Passa o escritor para persistir novos dados no cache
                )

                if user_vector:
                    writer_profile.writerow(user_vector)
                    # print(f"  -> Perfil salvo para {username}.")
                # else:
                    # print(f"  -> Falha/Sem dados relevantes para {username}.")

    print(f"\nPipeline concluído!")
    print(f"Cache de Animes atualizado: {len(anime_cache)} itens.")
    print(f"Perfis de Usuário salvos em {PROFILES_OUTPUT_FILE}.")

if __name__ == "__main__":
    try:
        run_pipeline()
    except KeyboardInterrupt:

        print("\nProcesso interrompido pelo usuário. Dados parciais salvos.")
