# Architecture

## Bird's Eye View

![Network Graph](/docs/network.drawio.svg)

You can think of Eventfully as a meta search engine for event websites with additional social features.
When a user searches for something, he gets a direct and more importantly fast answer from the no sql event database. In the background, the app then passes the search to its other sources to get their events and integrate them into the database for further searches. Some sources allow to get all stored events at once. They are contacted in a specified time interval and also integrated into our own database.

## Code Map

### eventfully/

All code needed to run the application, including the frontend.

### eventfully/database

Contains all the logic for communicating with and managing the databases and their connections needed to run the application.

- `crud` (create, write, update, delete): methods for performing all kinds of operations on the database.

- `database`: configuration of connections to the database

- `models`: classes that represent and specify the tables and documents of the databases

- `schemas`: classes that represent the structure of database tables and documents without being directly connected to a database.

### eventfully/search

Contains all the logic to get the events from our sources in our own format with as much data as we can get. We get the data using three different methods.

- `crawl`: extracts ALL data from a source in regular intervals, useful for sources where you can easily get all events at once.

- `search`: get specific events only when a user searches for them in our frontend. needs to be fast. good for sites that only provide a search themselves.

- `post_process`: more detailed analysis of events found by search that couldn't be fully fetched due to speed requirements.

### eventful/static

Static, mostly binary files for the site that don't change often, including images or css.  

### eventfully/templates

The HTML and jinja2 templates used by the application to render the frontend website, mostly on the server.  

### eventfully/main.py

The main entry point for the application, which defines most of the http routes and apis.  

### tests/

Mostly Python code that tests the main application in `eventfully/`.  

### .github/workflows

Various CI/CD scripts that perform automated tasks on GitHub such as docker image building, quality control, and code linting.  

### Dockerfile

A file with machine-readable instructions for building a Docker image containing the packaged and executable project for easy setup on other machines.  

### pyproject.toml

The configuration file for Python dependency management and some tool-specific configuration, manly Rye. Used to specify required Python packages, includes easily accessible scripts for developers and some linter configuration.  

### tailwind.config.css

Configuration for TailwindCSS on how to build the CSS for the frontend, including additional plugins used.
