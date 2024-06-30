## Running In Production

1. Install [Docker](https://docs.docker.com/engine/install/) and Docker Compose.
- ``curl -fsSL https://get.docker.com -o get-docker.sh ``
- ``sh get-docker.sh``
2. Verify if Docker was Installed sucessfully
- ``docker run hello-world``
3. Install Git
- Example Debian/Ubuntu: ``apt-get install git``
4. Clone or download Eventfully repository
- `` git clone https://github.com/BytezoTeam/Eventfully.git ``
5. Change Directory into the cloned git repository
- ``cd Eventfully``
6. Insert a secure Meilisearch key in the marked places in the `docker-compose.yml` file
7. Start the server
- `docker compose up`
8. Use Broswer and visit the website at ``http://localhost:80`` (replace localhost with an IP-Address if the container is not started locally)
