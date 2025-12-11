import requests
from bs4 import BeautifulSoup
import re
import time
import csv

def extract_work(work_id, work_type="manga"):
    """
    Extrai informações essenciais (nome, score, gêneros e tipo) de um mangá/manhwa/LN
    e filtra aqueles que já foram adaptados para anime.
    """
    url = f"https://myanimelist.net/{work_type}/{work_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, "lxml") 
        
        # Extrai e trata os títulos e gêneros dos mangás removendo outros textos irrelevantes da barra de títulos
        nome_tag = soup.find("title")
        nome = None
        if nome_tag:
            nome_completo = nome_tag.get_text(strip=True).replace(" - MyAnimeList.net", "")
            nome = nome_completo.split('|')[0].strip()

        # Checa se o mangá já foi adaptado para mídia animada.
        if work_type == "manga":
            relation_tags = soup.find_all("div", class_="relation")
            if relation_tags:
                for tag in relation_tags:
                    tag_text = tag.get_text(strip=True)
                    if "Adaptation" in tag_text and (
                        "(TV)" in tag_text or 
                        "(Movie)" in tag_text or 
                        "(OVA)" in tag_text or 
                        "(Special)" in tag_text or 
                        "(ONA)" in tag_text
                    ):
                        print(f"IGNORADO: {nome} (Já possui adaptação).")
                        return None 
        
        # Obtêm a Nota média do mangá
        score = None
        score_tag = soup.find("span", {"itemprop": "ratingValue"})
        if score_tag:
            score = score_tag.get_text(strip=True)

        # Obtêm os gêneros do mangá
        generos = []
        genero_tag = soup.find("span", string=lambda t: t and ('Genre:' in t or 'Genres:' in t)) 
        if genero_tag:
            parent = genero_tag.find_parent("div")
            if parent:
                generos = [
                    a.get_text(strip=True) 
                    for a in parent.find_all("a") 
                    if a.get('href') and ('/genre/' in a.get('href') or '/themes/' in a.get('href'))
                ]

        # Obtêm o tipo da obra (manhua e manhwa são considerados o mesmo tipo)
        tipo = None
        tipo_tag = soup.find("span", string=lambda t: t and 'Type:' in t)
        if tipo_tag:
            parent = tipo_tag.find_parent("div")
            if parent:
                a_tag = parent.find("a")
                if a_tag:
                    tipo = a_tag.get_text(strip=True)
        if tipo:
            s = tipo.strip().lower()
            if s == "Manhua":
                tipo = "Manhwa"
        # Estrutura do dicionário final para criação do csv
        work_data = {
            "id": work_id,
            "nome": nome,
            "score": score,
            "generos": ", ".join(generos) if generos else "None",
            "tipo": tipo if tipo else "None" 
        }
        
        return work_data

    except requests.exceptions.RequestException as e:
        print(f"    ⚠️ Erro de Rede/HTTP ao acessar {url}: {e}")
        return None
    except Exception as e:
        print(f"    ⚠️ Erro inesperado durante o parsing de {url}: {e}")
        return None

# Extração dos IDs de uma página de Browse do MAL

def extrair_ids_ranking(url_base, limite_total, step=50):
    """Extrai IDs de anime/manga a partir de páginas de ranking do MAL."""
    
    lista_ids = []
    for limit in range(0, limite_total + 1, step):
        url = f"{url_base}{limit}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            
            links_titulo = soup.select('a.hoverinfo_trigger.fs14.fw-b')
            
            if not links_titulo:
                links_titulo = soup.select('.ranking-list .manga-title a')
                if not links_titulo:
                     links_titulo = soup.select('.ranking-list .anime-title a')

            if not links_titulo:
                break 

            for tag_a in links_titulo:
                href = tag_a.get('href')
                if href:
                    match = re.search(r"/(anime|manga)/(\d+)/", href)
                    if match:
                        anime_id = match.group(2)
                        if anime_id not in lista_ids:
                            lista_ids.append(anime_id)
                            
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {url}: {e}")
            
        time.sleep(2) 
        
    return lista_ids

# Função main

if __name__ == "__main__":
    
    # Define o URL exato usado para extração (browse mangás by score)
    URL_MANGA_BASE = "https://myanimelist.net/topmanga.php?limit="
    LIMITE = 9400 # 9400 é aproximadamente o número de mangás de nota > 7, verificado manualmente
    
    # extrair ids com base nos parâmetros passados
    manga_ids = extrair_ids_ranking(URL_MANGA_BASE, limite_total=LIMITE)
    print(f"\n--- Total de IDs de mangá a processar: {len(manga_ids)} ---")

    # Extrair os dados com base em cada ID extraído
    csv_filename = "mangas_dados_essenciais.csv"
    fieldnames = ["id", "nome", "score", "generos", "tipo"]

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, manga_id in enumerate(manga_ids):
            # Passando o ID para a função refatorada
            dados_manga = extract_work(manga_id, work_type="manga") 
            
            if dados_manga and dados_manga['nome']:
                writer.writerow(dados_manga)
                print(f"[{i+1}/{len(manga_ids)}] Sucesso: {dados_manga['nome']}")
            else:
                print(f"[{i+1}/{len(manga_ids)}] Falha ao obter dados para o ID: {manga_id}")
            
            # Sleep para o IP não ser banido pelo MAL
            time.sleep(2) 

    print(f"\nExtração completa! Dados salvos em {csv_filename}")