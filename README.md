# Eventfully
![image](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white) ![image](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white) ![image](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white) ![img](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) ![img](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white) ![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white)![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

Eventfully is a Python-based web-application designed to process and show various events in your area

## Statistics
![image](https://img.shields.io/github/issues-search/BytezoTeam/Eventfully?query=is%3Aissue%20is%3Aclosed%20&style=flat-square&label=Closed%20Issues)
![image](https://github.com/BytezoTeam/Eventfully/actions/workflows/codeql.yml/badge.svg?style=flat-square)
![image](https://tokei.rs/b1/github/BytezoTeam/Eventfully)
![image](https://tokei.rs/b1/github/BytezoTeam/Eventfully?category=files)

## Development Setup
### 1. Clone or Download Eventfully
- Download Eventfully from GitHub or clone the repository with `git clone https://github.com/BytezoTeam/Eventfully` from your Terminal with [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- Open the Project in your Terminal or in your Files
  
### 2. Install Meilisearch (Search Database Server)
- [install and run Meilisearch](https://www.meilisearch.com/docs/learn/getting_started/installation)
- note down master key and server url in the .env file
  
### 3. Make the .env File

The file must be named `.env` and should be located in the root of the project (the same file level as `README.md` file).
It should contain this information (replace values with yours):

```
OPENAI_API_KEY="<openai api key>"
MEILI_KEY="<meilisearch master key>"
MEILI_HOST="<address of the meilisearch server e.g. http://localhost:7700>"
```
### 4. Install Rye
- install [Rye](https://rye-up.com/guide/installation/)
- run `rye sync` inside the folder to install the required python packages

### 5. Run Eventfully
- start the server with `rye run dev` or use `rye run main` (Only on Windows) to start the startup program

## Tech Stack
- [Bootstrap](https://getbootstrap.com/) for CSS (frontend)
- [HTMX](https://htmx.org/) for client-server interactions and reactivity (frontend)
- Python (backend)
- [Flask](https://flask.palletsprojects.com/) as web framework (backend)
- [peewee](https://docs.peewee-orm.com/en/latest/) as ORM with SQLite (backend)
- [meilisearch](https://www.meilisearch.com/) as the database for the search (backend)
- [OpenAI API](https://openai.com/product) for the classification of events (backend)
