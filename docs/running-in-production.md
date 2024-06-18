## Running In Production

1. install [Docker](https://docs.docker.com/engine/install/) and Docker Compose.
- ``curl -fsSL https://get.docker.com -o get-docker.sh ``
- ``sh get-docker.sh``
2. Verify if Docker was Installed sucessfully
- ``docker run hello-world``
3. Install Git
- Example Debian/Ubuntu: ``apt-get install git``
4. clone or download Eventfully repository
- `` git clone https://github.com/BytezoTeam/Eventfully.git ``
5. insert a secure Meilisearch key in the marked places in the `docker-compose.yml` file
6. start the sever by running `docker compose up` in your terminal inside the Eventfully folder
7. Use Broswer and visit the website at ``http://<localhost:XXX``
