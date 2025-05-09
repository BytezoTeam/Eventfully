# Architecture

## Bird's Eye View

```mermaid
architecture-beta
    service user(internet)[User]

    service sources(internet)[Sources]

    group server(server)[Server]

    service sql(database)[SQL DB] in server
    service meilisearch(database)[Meilisearch] in server
    service flask(server)[Flask Server] in server
    service scraper(server)[Scraper] in server

    junction db in server

    flask:L -- R:db
    db:T -- B:sql
    db:B -- T:meilisearch
    user:L -- R:flask
    scraper:L -- R:meilisearch
    scraper:R -- L:sources
```

You can think of Eventfully as a meta search engine for event websites with additional social features.
When a user searches for something, he gets a direct and more importantly fast answer from the no sql event database. In the background, the crawler crawls all specified sources once a day and adds them to the database.

## Code Map

### eventfully/

All code needed to run the application, including the frontend.

### eventfully/database/

Contains all the logic for communicating with and managing the databases and their connections needed to run the
application.

- `crud` (create, write, update, delete): methods for performing all kinds of operations on the database.

- `database`: configuration of connections to the database

- `models`: classes that represent and specify the tables and documents of the databases

- `schemas`: classes that represent the structure of database tables and documents without being directly connected to a
  database.

### eventfully/search.py

Contains the search logic aka. querying meilisearch.

### eventfully/crawl/

Contains all the logic to get the events from our sources in our own format with as much data as we can get through web crawling in a specific time interval.
The crawling for a source can be entirely self coded or the `auto_crawl` module can be used as a building block system for a scraper.

### eventfully/static/

Static, mostly binary files for the site that don't change often, including images or css.

### eventfully/templates/

The HTML and jinja2 templates used by the application to render the frontend website, mostly on the server.

### eventfully/main.py

The main entry point for the application. Starts the flask server, database and the crawler.

### eventfully/routes/

All web-accessible routes for users and APIs, loosely separated into files by function.

### tests/

Mostly Python code that tests the main application in `eventfully/`.

### .github/workflows/

Various CI/CD scripts that perform automated tasks on GitHub such as docker image building, quality control, and code
linting.

### Dockerfile

A file with machine-readable instructions for building a Docker image containing the packaged and executable project for
easy setup on other machines.

### pyproject.toml

The configuration file for Python dependency management and some tool-specific configuration, manly Rye. Used to specify
required Python packages, includes easily accessible scripts for developers and some linter configuration.

### tailwind.config.css

Configuration for TailwindCSS on how to build the CSS for the frontend, including additional plugins used.
