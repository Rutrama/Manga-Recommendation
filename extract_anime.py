import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import os

ANIME_CACHE_FILE = "animes_cache.csv"
ANIME_CACHE_FIELDNAMES = ["id", "nome", "generos", "source"]

def extract_anime_data(anime_id):
    """ Extrai informações essenciais (nome, score, gêneros e source(tipo)) de um anime."""
    url = f"https://myanimelist.net/anime/{anime_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, "lxml") 
        
        # Extrai e trata os títulos e gêneros dos animes
        nome = soup.find("title").get_text(strip=True).replace(" - MyAnimeList.net", "").split('|')[0].strip()
        generos = [a.get_text(strip=True) for a in soup.find("span", string=lambda t: t and ('Genre:' in t or 'Genres:' in t)).find_parent("div").find_all("a")]
        
        # Extrai a fonte original da Obra
        source = None
        source_tag = soup.find("span", string=lambda t: t and 'Source:' in t)
        if source_tag:
            full_text = source_tag.find_parent("div").get_text(strip=True)
            source = full_text.replace("Source:", "").strip()

        return {
            "id": anime_id,
            "nome": nome,
            "generos": ", ".join(generos) if generos else "None",
            "source": source if source else "None" 
        }

    except Exception as e:
        print(f"Erro ao extrair anime {anime_id}: {e}")
        return None

def load_anime_cache(filename="animes_cache.csv"):
    """Carrega o cache de animes existentes para evitar requisições no MAL."""
    cache = {}
    try:
        with open(filename, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader) # Pula o cabeçalho
            for row in reader:
                if len(row) >= 4:
                     cache[row[0]] = {"generos": row[2].split(", "), "source": row[3]}
        print(f"Cache de animes carregado: {len(cache)} itens.")
    except FileNotFoundError:
        print("Cache de animes não encontrado. Será criado um novo.")
    return cache

def initialize_cache_file():
    """Cria o arquivo de cache de animes se ele não existir."""
    if not os.path.exists(ANIME_CACHE_FILE) or os.stat(ANIME_CACHE_FILE).st_size == 0:
        with open(ANIME_CACHE_FILE, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(ANIME_CACHE_FIELDNAMES)
        print(f"Arquivo de cache ({ANIME_CACHE_FILE}) inicializado.")