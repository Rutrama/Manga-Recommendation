import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime
import os 

def extrair_pagina_usuarios(page_number):
    """Extrai todos os usuários de uma única página e seus status de atividade."""
    
    # Base URL com filtro de localização (Brasil)
    BASE_URL = "https://myanimelist.net/users.php?cat=user&q=&loc=Brazil&agelow=0&agehigh=0&g="
    usuarios_encontrados = []
    
    show_offset = (page_number - 1) * 24 
    url = f"{BASE_URL}&show={show_offset}"
    print(f"-> Extraindo usuários da Página {page_number} (Offset: {show_offset})")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        
        user_data_cells = soup.select('td[align="center"].borderClass')
        
        if not user_data_cells:
            return usuarios_encontrados, False # Fim da lista
        
        for cell in user_data_cells:
            username_tag = cell.select_one('div a[href^="/profile/"]')
            last_online_tag = cell.select_one('div.spaceit_pad small')
            
            if username_tag and last_online_tag:
                username = username_tag.get_text(strip=True)
                last_online = last_online_tag.get_text(strip=True)
                
                usuarios_encontrados.append({
                    "username": username,
                    "last_online": last_online
                })
        
        return usuarios_encontrados, True
            
    except requests.exceptions.RequestException as e:
        print(f"Erro ao acessar {url}: {e}")
        return usuarios_encontrados, True

def check_activity(date_string, min_year):
    """
    Função para verificar se a data de status de atividade extraída de um usuário é mais recente que o threshold
    """
    date_string = date_string.lower()
    
    # Checa se houve Atividade Recente pelas strings "minutes ago", "yesterday", "today"
    if "ago" in date_string or "today" in date_string or "yesterday" in date_string:
        return True
    
    # Checa o Ano da data acesso diretamente
    current_year = int(time.strftime("%Y"))
    for year in range(min_year, current_year + 2):
        if str(year) in date_string:
            return True
    
    try:
        match = re.search(r'\d{4}', date_string)
        if match:
            year = int(match.group(0))
            if year >= min_year:
                return True
    except Exception:
        pass

    return False

def salvar_usuarios_em_csv(usuarios, filename, append=False):
    """Salva a lista de usuários em um arquivo CSV."""
    file_exists = os.path.exists(filename) and os.stat(filename).st_size > 0
    mode = 'a' if append and file_exists else 'w'
    
    with open(filename, mode=mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        
        if not file_exists or not append:
            writer.writerow(["username"])
        
        for user in usuarios:
            writer.writerow([user])

# função main para extração separada

if __name__ == "__main__":
    
    # Definir o número de usuários extraídos e o ano mínimo de atividade
    USUARIO_GOAL = 1000
    ANO_MINIMO_ATIVIDADE = 2017 
    
    USUARIOS_OUTPUT_FILE = f"usernames_{ANO_MINIMO_ATIVIDADE}.csv"
    current_page = 1 
    usuarios_ativos_encontrados = set() 
    
    print(f"Configuração: Meta={USUARIO_GOAL} | Atividade Mínima: {ANO_MINIMO_ATIVIDADE}")
    
    # Loop de Extração
    while len(usuarios_ativos_encontrados) < USUARIO_GOAL:
        
        # Extrair a página atual
        page_data, has_more = extrair_pagina_usuarios(current_page)
        
        # Processar usuários e checar a meta
        novos_usuarios_ativos = []
        for user in page_data:
            
            # chamada da função de atividade
            if check_activity(user["last_online"], ANO_MINIMO_ATIVIDADE):
                username = user["username"]
                if username not in usuarios_ativos_encontrados:
                    usuarios_ativos_encontrados.add(username)
                    novos_usuarios_ativos.append(username)
                    print(f"Ativo (Total: {len(usuarios_ativos_encontrados)}/{USUARIO_GOAL}): {username} (Último acesso: {user['last_online']})")
                
                # Checa a meta APÓS adicionar o usuário
                if len(usuarios_ativos_encontrados) >= USUARIO_GOAL:
                    break
        
        # C. Salvar os novos usuários ativos encontrados no CSV
        if novos_usuarios_ativos:
            salvar_usuarios_em_csv(novos_usuarios_ativos, USUARIOS_OUTPUT_FILE, append=True)
            print(f" {len(novos_usuarios_ativos)} novos usuários foram salvos. ...")
        
        # D. Verificar condições de parada do loop WHILE
        if len(usuarios_ativos_encontrados) >= USUARIO_GOAL:
            print(f"\nMeta de {USUARIO_GOAL} usuários ativos atingida! ---")
            break
            
        if not has_more:
            # Se terminou a lista E não atingiu a meta, informa.
            print("\nFim da lista de usuários na região 'Brasil'. Não foi possível atingir a meta.")
            print(f"Tente mudar o ANO_MINIMO_ATIVIDADE (atualmente {ANO_MINIMO_ATIVIDADE}) para um ano anterior.")
            break
        
        # E. Preparar para a próxima iteração e sleep para evitar ban
        current_page += 1
        time.sleep(3) 

    # resultado final da extração
    print(f"\nTotal final de usuários ativos encontrados: {len(usuarios_ativos_encontrados)}")
    print(f"Lista de usuários ativos salva em {USUARIOS_OUTPUT_FILE}")