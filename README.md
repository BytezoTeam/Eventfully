# Eventfully
![sqlite batch](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white) ![tailwindcss batch](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white) ![flask batch](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white) ![pyhton batch](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue) ![html batch](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white) ![chatgpt batch](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white) <br>
![closed issues batch](https://img.shields.io/github/issues-search/BytezoTeam/Eventfully?query=is%3Aissue%20is%3Aclosed%20&style=flat-square&label=Closed%20Issues) ![codeql status batch](https://github.com/BytezoTeam/Eventfully/actions/workflows/codeql.yml/badge.svg?style=flat-square) ![total lines batch](https://tokei.rs/b1/github/BytezoTeam/Eventfully) ![files batch](https://tokei.rs/b1/github/BytezoTeam/Eventfully?category=files)

Eventfully is a python based web-application designed to process and show various events in your area

## Techstack
- [TailwindCSS](https://tailwindcss.com/) for CSS (frontend)
- [HTMX](https://htmx.org/) for client-server interactions and reactivity (frontend)
- Python (backend)
- [Flask](https://flask.palletsprojects.com/) as web framework (backend)
- [peewee](https://docs.peewee-orm.com/en/latest/) as ORM with SQLite (backend)
- [meilisearch](https://www.meilisearch.com/) as the database for the search (backend)
- [OpenAI API](https://openai.com/product) for the classification of events (backend)

## Our Sources
- [Zuerichunbezahlbar](https://www.zuerichunbezahlbar.ch/events/): Events for Zürich in Switzerland
- [Eventim](https://www.eventim.de/): Events for Germany
- [Kulturlöwen](https://www.kulturloewen.de): Events in Velbert, a small City near Essen, Germany

## Development Setup
### 1. Clone or Download Eventfully
- download Eventfully from GitHub or clone the repository with `git clone https://github.com/BytezoTeam/Eventfully` from your terminal with [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed
- open the project in your terminal or in your files
  
### 2. Install Meilisearch (Search Database Server)
- [install and run Meilisearch](https://www.meilisearch.com/docs/learn/getting_started/installation)
- note down master key and server url in the .env file
  
### 3. Make a .env File

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

### 6. Add Test-Data to Eventfully (Optional)
- Run the `injectTestDataGUI.py` (GUI Version) or `injectTestDataTerminal.py` (Termainal Version) Script in the [Tests](https://github.com/BytezoTeam/Eventfully/tree/main/tests) Folder
  #### In the GUI-Application
- Paste Test-Data in a .json format in the GUI-Textbox
- Press the 'Inject' button
  - Pasted Test-Data must contain:
    ```
    'title': Title as a string
    'description': Description as a string
    'link': Link as a string
    'price': Price for the event as a string
    'tags': Tags as a list
    'start_date': Start Date as a string and %d-%m-%Y %H:%M:%S format
    'end_date': End Date as a string and %d-%m-%Y %H:%M:%S format
    'age': Age as a string
    'accessibility': Accessibility as a string
    'address': Address as a string
    'city': City as a string
    ```
  - You can paste multiple Events at the same time
  - Some Test-Data is available [here](https://github.com/BytezoTeam/Eventfully/blob/main/tests/test-data.json)
  - Check that the data was injected successfully, by opening the Meilisearch Dashboard. The Data should be displayed there

#### For the Terminal Version 
- Paste a vaild .json file path into the console, if you want to use your own Test-Data (Must contain the values listed on top)
  or
- Press enter, and [this](https://github.com/BytezoTeam/Eventfully/blob/main/tests/test-data.json) Test-Data will be injected autmaticly

## License
[GPL-3.0](/LICENSE.txt)
