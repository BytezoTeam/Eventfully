# Eventfully

## Development Setup
### Meilisearch (Search Database Server)
- [install and run Meilisearch](https://www.meilisearch.com/docs/learn/getting_started/installation)
- note down master key and server url in the [.env file](/docs/dot-env.md)
# .env File

The file must be named `.env` and should be located in the root of the project (the same file level as `README.md` file).

```
OPENAI_API_KEY="<openai api key>"
MEILI_KEY="<meilisearch master key>"
MEILI_HOST="<address of the meilisearch server e.g. http://localhost:7700>"
```

### Python
- install [Rye](https://rye-up.com/guide/installation/)
- run `rye sync` inside the folder to install the required python packages
- start the server with `rye run dev`

## Tech Stack
- [Bootstrap](https://getbootstrap.com/) for CSS (frontend)
- [HTMX](https://htmx.org/) for client-server interactions and reactivity (frontend)
- Python (backend)
- [Flask](https://flask.palletsprojects.com/) as web framework (backend)
- [peewee](https://docs.peewee-orm.com/en/latest/) as ORM with SQLite (backend)
- [meilisearch](https://www.meilisearch.com/) as the database for the search (backend)
- [OpenAI API](https://openai.com/product) for the classification of events (backend)
