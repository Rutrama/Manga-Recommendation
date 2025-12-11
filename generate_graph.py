import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from networkx.algorithms.community import greedy_modularity_communities


###############################################
# GRAPH GENERATOR — CLUSTERIZAÇÃO DE PERFIS  #
###############################################

def load_profiles(path: str) -> pd.DataFrame:
    """Carrega o csv e prepara um DataFrame de perfis."""
    df = pd.read_csv(path)
    df = df.set_index("username")
    return df


def normalize_percent(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza cada linha (usuário) em percentuais."""
    return df.div(df.sum(axis=1), axis=0)


def compute_similarity(df_norm: pd.DataFrame) -> pd.DataFrame:
    """Gera a matriz de similaridade por cosseno."""
    sim = cosine_similarity(df_norm)
    sim_df = pd.DataFrame(sim, index=df_norm.index, columns=df_norm.index)
    return sim_df


def build_graph(sim_df: pd.DataFrame, threshold: float = 0.35) -> nx.Graph:
    """Constrói o grafo conectando usuários com similaridade acima do limite."""
    G = nx.Graph()

    users = sim_df.index.tolist()

    for i, u in enumerate(users):
        for j in range(i + 1, len(users)):
            v = users[j]
            score = sim_df.loc[u, v]
            if score >= threshold:
                G.add_edge(u, v, weight=score)

    return G


def detect_communities(G: nx.Graph):
    """Agrupa usuários usando modularidade gulosa."""
    if len(G.nodes) == 0:
        return []

    comms = greedy_modularity_communities(G)

    # Converte para lista de listas
    return [list(c) for c in comms]


def describe_community(df, users):
    """Gera uma descrição da comunidade para uso na descrição do grafo e no arquivo de output."""
    source_cols = [c for c in df.columns if c.startswith("Source_")]
    genre_cols  = [c for c in df.columns if c.startswith("Genre_")]

    sub = df.loc[users]
    rest = df.drop(users)

    mean_sub = sub.mean()
    mean_rest = rest.mean()

    # diferenças (quanto esse gênero é característico da comunidade)
    diff = mean_sub[genre_cols] - mean_rest[genre_cols]
    top_genres = diff.sort_values(ascending=False).head(2).index
    top_genres = [g.replace("Genre_", "") for g in top_genres]

    # para source: mesmo processo
    diff_src = mean_sub[source_cols] - mean_rest[source_cols]
    top_source = diff_src.idxmax().replace("Source_", "")

    return {
        "source": top_source,
        "genres": top_genres,
        "n_users": len(users)
    }

def generate_community_names(df, comms, top_k=2):
    """
    Gera nomes determinísticos para cada comunidade e Retorna lista de comunidades já nomeadas
    """
    source_cols = [c for c in df.columns if c.startswith("Source_")]
    genre_cols  = [c for c in df.columns if c.startswith("Genre_")]

    # Precompute means for efficiency
    overall_mean = df.mean()

    names = []
    taken = set()

    for comm in comms:
        if len(comm) == 0:
            names.append("Comunidade Vazia")
            continue

        sub = df.loc[comm]
        mean_sub = sub.mean()
        diff = (mean_sub[genre_cols] - (overall_mean[genre_cols])).sort_values(ascending=False)

        ordered_genres = [g.replace("Genre_", "") for g in diff.index.tolist() if diff[g] > -1e9]  # preserve order

        chosen = ordered_genres[:top_k]
        chosen = [g.replace("_", " ") for g in chosen]

        # adicione o melhor gênero
        candidate = " / ".join(chosen) if chosen else "SemGênero"
        idx = top_k
        while candidate in taken and idx < len(ordered_genres):
            # adicione o segundo melhor gênero
            extra = ordered_genres[idx].replace("_", " ")
            candidate = " / ".join(chosen + [extra])
            idx += 1

        # se não for uma combinação única, adicione o próximo gênero que gere uma combinação única.
        if candidate in taken:
            suffix = 2
            while f"{candidate} ({suffix})" in taken:
                suffix += 1
            candidate = f"{candidate} ({suffix})"

        taken.add(candidate)
        names.append(candidate)

    return names

from collections import defaultdict

def draw_graph(G, communities, df, community_names=None, output="graph.png"):
    """
    Gera imagem PNG do grafo com cores por comunidade e legenda com gêneros.
    """

    import matplotlib.colors as mcolors
    if len(G.nodes) == 0:
        print("Grafo vazio — nada para desenhar.")
        return

    # Define Layout do grafo
    pos = nx.spring_layout(G, seed=42, k=0.3, iterations=50)

    # Cores base (TABLEAU)
    base_colors = list(mcolors.TABLEAU_COLORS.values())
    n_base = len(base_colors)
    n_comms = len(communities)

    # Gerar cores extras, caso necessário (+10 comunidades)
    extra_colors = []
    if n_comms > n_base:
        import colorsys
        
        n_needed = n_comms - n_base
        def generate_colors(n):
            return [
                colorsys.hsv_to_rgb(i / n, 0.65, 0.95)
                for i in range(n)
            ]

        extra_colors = generate_colors(n_needed)

    all_colors = base_colors + extra_colors


    # Mapear nó → cor (cada comunidade recebe sua cor correspondente)
    node_colors = {}
    for i, comm in enumerate(communities):
        color = all_colors[i]  # agora é seguro
        for user in comm:
            node_colors[user] = color

    node_color_list = [node_colors.get(n, (0.6,0.6,0.6)) for n in G.nodes()]
    node_sizes = [40] * len(G.nodes())

    plt.figure(figsize=(20, 12))

    # Desenhar grafo
    nx.draw_networkx_nodes(G, pos, node_color=node_color_list, node_size=node_sizes)
    nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.5)

    plt.axis("off")
    plt.title("Grafo de Similaridade entre Usuários (Comunidades por Cor)", fontsize=18)

    # Se community_names não fornecido, gere
    if community_names is None:
        community_names = generate_community_names(df, communities, top_k=2)

    #  gerar legenda do grafo
    from matplotlib.patches import Patch
    legend_elements = []

    for i, comm in enumerate(communities):
        label = community_names[i]
        color = all_colors[i]
        legend_elements.append(
            Patch(facecolor=color, edgecolor='black',
                label=f"{label} ({len(comm)} usuários)")
    )

    plt.legend(
        handles=legend_elements,
        title="Comunidades (gêneros dominantes)",
        fontsize=10,
        title_fontsize=12,
        loc="upper left",
        bbox_to_anchor=(1, 1)
    )

    plt.tight_layout()
    plt.savefig(output, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"\n📁 Imagem salva como: {output}")



# função main
def main(file_path: str, threshold: float = 0.35):
    print("Carregando perfis...")
    df = load_profiles(file_path)

    print("Normalizando dados em percentuais...")
    df_norm = normalize_percent(df)

    # aplicando TF-IDF nos gêneros para diminuir o peso dos gêneros extremamente populares
    from sklearn.feature_extraction.text import TfidfTransformer

    genre_cols = [c for c in df_norm.columns if c.startswith("Genre_")]

    print("Aplicando TF-IDF nos gêneros...")
    tfidf = TfidfTransformer(norm='l2', use_idf=True)
    df_norm[genre_cols] = tfidf.fit_transform(df_norm[genre_cols]).toarray()

    # aumentando o peso das sources para elas aparecerem no resultado
    print("Ajustando peso de fontes...")
    source_cols = [c for c in df_norm.columns if c.startswith("Source_")]
    df_norm[source_cols] = df_norm[source_cols] * 1.5

    # calculando similaridade de cosseno
    print("Calculando similaridade entre usuários...")
    sim_df = compute_similarity(df_norm)


    # constrói o grafo
    print(f"Construindo grafo com threshold = {threshold}...")
    G = build_graph(sim_df, threshold)

    print(f"Nó(s): {len(G.nodes)}  —  Arestas: {len(G.edges)}")

    print("Detectando comunidades...")
    comms = detect_communities(G)

    print(f"Encontradas {len(comms)} comunidades.")

    # Gera nomes para output
    community_names = generate_community_names(df, comms, top_k=2)

    for i, c in enumerate(comms):
        # detalhe para console: ainda mostramos origem + top genres segundo describe_community
        desc = describe_community(df, c)
        print(f"\n[{community_names[i]}] ({desc['n_users']} usuários)")
        print(f"  > Foco Principal: Origem - {desc['source']}. Gêneros - {', '.join(desc['genres'])}")

    # desenha o grafo usando exatamente os mesmos nomes
    draw_graph(G, comms, df, community_names=community_names, output="graph.png")

    return G, comms

if __name__ == "__main__":
    FILE = "profiles.csv"
    THRESHOLD = 0.98
    main(FILE, THRESHOLD)

