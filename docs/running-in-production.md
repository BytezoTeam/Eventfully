## Running In Production

1. Install [Docker](https://docs.docker.com/engine/install/) and Docker Compose.
   - `curl -fsSL https://get.docker.com -o get-docker.sh`
   - `sh get-docker.sh`
2. Verify if Docker was Installed sucessfully
   - `docker run hello-world`
4. Get the [docker-compose.yml file](https://github.com/BytezoTeam/Eventfully/blob/main/docker-compose.yml) from the Eventfully repository
5. Replace placeholders for environment variables with fitting values
6. Start the server
   - `docker compose up`
7. Use Browser and visit the website at `http://localhost` (replace localhost with an IP-Address if the container is not started locally)
