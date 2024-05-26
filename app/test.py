from python_on_whales import DockerClient

docker = DockerClient(compose_files=["../submission/testing-challange/docker-compose.yml"])

docker.compose.build()
docker.compose.up(detach=True)
# docker.compose.down()

'''
docker run -d --name app_con testing-challange-app
docker run -d --name db_con testing-challange-db

docker network create my_network
docker run --name app_con --network my_network testing-challange-app
docker run --name db_con --network my_network testing-challange-db
'''