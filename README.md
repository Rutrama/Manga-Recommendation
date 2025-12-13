# Manga-Recommendation
 O projeto desenvolvido teve o intuito de analisar os gêneros atribuídos a diferentes animes e encontrar padrões de uso entre usuários que costumam classificar positivamente tais gêneros, de forma a encontrar combinações de gênero com potencial para criação de novas obras de entretenimento no futuro. Para tal, foi feita a raspagem de perfis da plataforma MyAnimeList diretamente, usando BeautifulSoup para obtenção dos mangás e shows, seus gêneros, assim como a mídia original daquela obra (mangá, light novel, manhwa ou diretamente para anime). Depois, o conjunto de obras e notas de cada usuário foi utilizado para calcular sua similaridade com outros usuários, aglomerando aqueles que possuem interesses similares em um grafo gerado. Por fim, o grafo foi usado para calcular possíveis associações de gêneros e permitiu a criação de recomendações de adaptações com potencial de atingir o maior número de usuários de uma comunidade.

---

### Estrutura do Projeto

Foram construídos **7 scripts em Python**:

- **extract_anime.py**  
    Contêm as funções que interagem com o `animes_cache.csv`, criando ou lendo o arquivo e armazenando novas entradas no vetor de animes com base no ID do anime fornecido.

- **extract_manga.py**  
    Script dedicado à implementação das funções de **raspagem de mangás**, responsável pela criação do arquivo `manga_cache.csv`.  
    Essa base contém mangás ainda não adaptados e é utilizada na **etapa final de recomendação** do projeto.

- **extract_users.py**  
    Implementa as funções de **raspagem de IDs de usuários**, criando o arquivo `usernames.csv`.  
    A base contém usuários ativos a partir de uma data especificada e serve como entrada para o script `profiler.py`.

- **normalizer.py**  
    Responsável pelas **funções de normalização dos dados**, além de conter parâmetros que definem como os dados serão tratados na criação do arquivo `profiles.csv`.  
    Inclui também a função que efetivamente gera esse arquivo.

- **profiler.py**  
    Utiliza as funções de `extract_anime.py`, o cache de animes gerado, e os IDs de usuários extraídos para analisar as características dos animes consumidos por cada usuário e gerar uma **assinatura única de perfil**.


- **graph_generator.py**  
    Contém as funções responsáveis pela **geração do grafo de usuários** e de suas visualizações.  
    As assinaturas de usuários são agrupadas com base em sua **similaridade**, sendo que as arestas do grafo representam a **similaridade de cosseno** entre dois usuários.

- **recommender.py**  
    Utiliza a base de dados de mangás e o grafo gerado para selecionar o **mangá com maior similaridade** a uma comunidade específica, realizando a recomendação final.

---

### Utilização

Assumindo-se que se queira apenas gerar as recomendações usando a base de mangás e perfis de usuários já fornecida:

#### 1. Pré-requisitos
- Certifique-se de ter o **Python 3.12** ou superior instalado em seu sistema.  
- O **PATH** deve estar configurado corretamente. 
- Certifique-se de que os arquivos `profiles.csv` e `mangas_cache.csv`, estejam na raiz do projeto.

#### Dependências
Para gerar assinaturas e grafos:

```bash
sudo apt-get install networkX louvain pandas
```

---

#### 2. Execução
Abra um terminal e navegue até o diretório raiz do projeto.  
Execute o comando:

```bash
python recommender.py
```
#### 3. Saída

Após a execução do projeto, será gerado na pasta raiz do projeto:

- O arquivo `output.dat` contendo as recomendações para cada comunidade.

- O arquivo `graph_comm.png` contendo uma representação gráfica do **grafo de comunidades** gerado.

### Extração Manual
**AVISO:** O processo de recriação da base de dados utilizada envolve e extração direta do site MyAnimeList, e consequentemente, é limitado pelo número de requisições aceitas pelo site. Assim, mesmo com as otimizações de cache implementadas, espera-se que o processo demore cerca de 6 horas.

Para realizar a extração manual dos dados com base no código fornecido deve-se seguir o seguinte processo

#### 1. Dependências Adicionais
Para gerar extrair os dados e criar assinaturas de usuário:

```bash
sudo apt-get install bs4 lxml tqdm requests
```

---

#### 2. Ordem de execução

Os scripts de extração devem ser executados na seguinte ordem:

extract_manga.py → extract_users.py → profiler.py → recommender.py

#### 3. Saída

Após a execução do projeto, serão gerados também na pasta raiz do projeto:

- O arquivo `mangas_cache.csv` contendo os mangás não adaptados extraídos do MyAnimeList.

- O arquivo `usernames.csv` contendo os nomes extraídos de contas **brasileiras** do MyAnimeList.

- O arquivo `animes_cache.csv` contendo os animes extraídos das listas dos perfis de usuário do MyAnimeList.

- O arquivo `profiles.csv` contendo as assinaturas de consumo dos perfis analisados.

Além das saídas do `recommender.py` já pontuadas anteriormente.

### Especificações do Teste
Os testes foram executados utilizando as seguintes especificações de máquina:

| Componente | Modelo / Especificação |
|-------------|------------------------|
| **Processador** | AMD Ryzen 3 4350G 3.8GHz|
| **Placa-mãe** | ASRock B450M Steel Legend |
| **Placa de video** | Radeon Graphics Vega 6 (Renoir)|
| **Memória RAM** | 32 GB Crucial Ballistix 3800MHz CL16|
| **Sistema Operacional** | MacOS Ventura 13.7.8 |
| **Versão do Python** | 3.12.1 |


# Autor

<table style="margin: 0 auto; text-align: center;">
  <tr>
    <td colspan="5"><strong>Aluno</strong></td>
  </tr>
  <tr>
      <td>
      <img src="https://avatars.githubusercontent.com/u/83346676?v=4" alt="Avatar de Arthur Santana" style="border-radius:50%; border:4px solid #4ECDC4; box-shadow:0 0 10px #4ECDC4; width:100px;"><br>
      <strong>Arthur Santana</strong><br>
      <a href="https://github.com/Rutrama">
        <img src="https://img.shields.io/github/followers/Rutrama?label=Seguidores&style=social&logo=github" alt="GitHub - Arthur Santana">
      </a>
    </tr>
    <tr>
        <td colspan="5"><strong>Professor</strong></td>
    </tr>
    <tr>
    <td colspan="5" style="text-align: center;">
      <img src="https://avatars.githubusercontent.com/u/46537744?v=4" alt="Avatar de Prof. Michel Pires" style="border-radius:50%; border:4px solid #00599C; box-shadow:0 0 10px #00599C; width:100px;"><br>
      <strong>Prof. Michel Pires</strong><br>
      <a href="https://github.com/mpiress">
        <img src="https://img.shields.io/github/followers/mpiress?label=Seguidores&style=social&logo=github" alt="GitHub - Prof. Michel Pires">
      </a>
    </td>
  </tr>
