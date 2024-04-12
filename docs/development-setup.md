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

```env
OPENAI_API_KEY="<openai api key>"
MEILI_KEY="<meilisearch master key>"
MEILI_HOST="<address of the meilisearch server e.g. http://localhost:7700>"
```

### 4. Install Node

- [Node Installation Instructions](https://nodejs.org/en/learn/getting-started/how-to-install-nodejs)

### 5. Install Node Dependencies

- run `npm install`

### 6. Build CSS

- run `npm run dev`

### 7. Install Rye

- [Rye Installation Instructions](https://rye-up.com/guide/installation/)

### 8. Install Python Dependencies

- run `rye sync`

### 9. Run Eventfully

- run `rye run dev`

### 10. Add Test-Data to Eventfully (Optional)

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
