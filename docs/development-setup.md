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
MEILI_MASTER_KEY="<meilisearch master key>"
MEILI_HOST="<address of the meilisearch server e.g. http://localhost:7700>"
IMPRINT="<imprint (optional)>"
```

### 4. Install Rye

- [Rye Installation Instructions](https://rye-up.com/guide/installation/)

### 5. Install Python Dependencies

- run `rye sync`

### 6. Build CSS

- run `rye run css-build` to build the CSS once OR
- run `rye run css-gen` to automatically re-build CSS on each modification the HTML files

### 7. Run Eventfully

- run `rye run dev`

### Voilà. Everything should now run
