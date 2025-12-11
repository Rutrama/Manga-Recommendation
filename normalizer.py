import requests
import time

def normalize_source(raw_source: str) -> str:
    if not raw_source:
        return "Other"
    s = raw_source.strip().lower()

    if "web manga" in s or "webmanga" in s:
        return "Manhwa"
    if "web novel" in s or "webnovel" in s:
        return "Light Novel"
    if "light novel" in s or "novel" in s:
        return "Light Novel"
    if "original" in s:
        return "Original"
    if "manhwa" in s:
        return "Manhwa"
    if "manhua" in s:
        return "Manhwa"
    if "manga" in s:
        return "Manga"

    return "Other"

# pesos por source
SOURCE_WEIGHTS = {
    "Manhwa": 2.0,
    "Light Novel": 1.8,
    "Original": 1.1,
    "Manga": 1.0,
    "Other": 0.8,
}

def create_user_profile(username, anime_cache, sources_alvo, generos_alvo, writer_cache):
    url = f"https://myanimelist.net/animelist/{username}/load.json?status=2"

    print(f"\n[USER: {username}] Coletando lista...")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        anime_list = response.json()
    except Exception as e:
        print(f"[ERRO] Falhou para {username}: {e}")
        return None

    if not isinstance(anime_list, list) or len(anime_list) == 0:
        print(f"[DEBUG] Lista vazia ou privada para {username}.")
        return None

    # acumuladores brutos
    source_scores = {s: 0 for s in sources_alvo}
    genre_scores = {g: 0 for g in generos_alvo}

    soma_total_scores = 0

    for item in anime_list:
        score = item.get("score")
        anime_id = item.get("anime_id")

        if score is None or score == 0:
            continue
        if score < 7:
            continue
        if not anime_id:
            continue

        anime_id = str(anime_id)

        # verificação do cache.
        if anime_id not in anime_cache:
            print(f"[CACHE MISS] ID {anime_id}")
            from extract_anime import extract_anime_data
            data = extract_anime_data(anime_id)
            time.sleep(2)

            if not data or not data.get("source"):
                continue

            anime_cache[anime_id] = {
                "generos": data["generos"].split(", "),
                "source": data["source"]
            }

            writer_cache.writerow([
                data["id"],
                data["nome"],
                data["generos"],
                data["source"]
            ])
        else:
            data = anime_cache[anime_id]
            # print(f"[CACHE HIT] ID {anime_id}")

        # normalização de fonte
        source_final = normalize_source(data.get("source"))

        # soma bruta de scores
        soma_total_scores += score

        # acumula scores ponderados das sources
        if source_final in source_scores:
            source_scores[source_final] += score

        # acumula scores dos gêneros
        for g in data.get("generos", []):
            if g in genre_scores:
                genre_scores[g] += score

    if soma_total_scores == 0:
        print(f"[DEBUG] Nenhum anime válido para {username}.")
        return None

    # ---------------- normalização final ----------------
    profile = {"username": username}

    # proporção dos gêneros
    for g in generos_alvo:
        raw = genre_scores[g]
        profile[f"Genre_{g.replace(' ', '_')}"] = raw / soma_total_scores

    # proporção das sources com peso
    for s in sources_alvo:
        raw = source_scores[s]
        weighted = raw * SOURCE_WEIGHTS.get(s, 1.0)
        profile[f"Source_{s.replace(' ', '_')}"] = weighted / soma_total_scores

    print(f"Perfil final criado para {username}.")
    return profile
