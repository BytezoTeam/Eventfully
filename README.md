# Eventfully

## Development Setup
### Meilisearch (Search Database Server)
- [install and run Meilisearch](https://www.meilisearch.com/docs/learn/getting_started/installation)
- note down master key and server url in the [.env file](/docs/dot-env.md)

### Python
- install [Rye](https://rye-up.com/guide/installation/)
- run `rye sync` inside the folder to install the required python packages
- activate the virtual environment with
  - `source .venv/bin/activate` on Linux
- run the server with `python3 -m eventfully.main` inside the virtual environment 