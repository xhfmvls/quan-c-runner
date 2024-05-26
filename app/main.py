import signal
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from python_on_whales import DockerClient
import docker
import asyncio
from pydantic import BaseModel
import os
import shutil
import time
import requests
import json

'''
TODO:
- ✅ buat mekanisme update app.js / main.py / dll (yang gw kepikiran sekarang kita buat .txt yang isinya nama file yang perlu diganti (pake txt aja biar kita nga perlu buat kolom baru di ERD :) ))
- jalanin testing payload
- ngitung performance (waktu build n testing)
- buat async sehingga bisa sekaligus beberapa (ini rada low prioritynya, karna yang penting adalah functionallity nya jalan dulu)
'''

class Submission(BaseModel):
    id: str
    challenge_id: str

app = FastAPI()

def get_container_port(container_id: str):
    client = docker.from_env()
    container = client.containers.get(container_id)
    ports = container.attrs["NetworkSettings"]["Ports"]

    for port_info, _ in ports.items():
        port = port_info.split("/")[0]
        host_port = ports[port_info][0]["HostPort"]
        return host_port
    return None

def get_container_id(image_tag: str):
    client = docker.from_env()
    for container in client.containers.list(all=True):
        if image_tag in container.image.tags:
            return container.id
    return None
    
def get_dir_data(file_path):
    try:
        with open(file_path, "r") as file:
            first_line = file.readline().strip()
            second_line = file.readline().strip()
            return first_line, second_line
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None, None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/create-submission")
async def create_submission(
        id: str = Form(...),
        challenge_id: str = Form(...),
        file: UploadFile = File(...)
    ):
    # Create the Submission instance from form data
    submission = Submission(id=id, challenge_id=challenge_id)
    submission_id = submission.id
    challenge_id = submission.challenge_id
    file_name = file.filename
    
    # Set the source and destination directories
    source_dir = os.path.join("challenges", challenge_id)
    destination_dir = os.path.join("submissions", submission_id)

    if not os.path.exists(source_dir):
        raise HTTPException(status_code=404, detail=f"Source directory not found: {source_dir}")

    if os.path.exists(destination_dir):
        shutil.rmtree(destination_dir)

    # Copy the source directory to the destination directory
    try:
        shutil.copytree(source_dir, destination_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while copying the directory: {e}")

    # Save the uploaded file to the destination directory
    replace_txt = os.path.join(destination_dir, "replace.txt")
    if os.path.exists(replace_txt):
        file_type, replace_file_name = get_dir_data(replace_txt)
        if file_type == file_name.split(".")[-1]:
            replace_file_path = os.path.join(destination_dir, "app", replace_file_name)
            with open(replace_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            raise HTTPException(status_code=400, detail=f"False Extension, should be {file_type} instead of {file_name.split('.')[-1]}")
    else:
        raise HTTPException(status_code=404, detail=f"Replace File not found")

    # Create the Docker client and build the Docker image
    try:
        docker = DockerClient(compose_files=[os.path.join(destination_dir, "docker-compose.yml")])
        docker.compose.build(quiet=True)
        docker.compose.up(detach=True, quiet=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the Docker client: {e}")

    # Get the container ID and port
    container_id = get_container_id(f"{submission_id}-app:latest")
    port = get_container_port(container_id)

    # Check if the application is running
    flag = False
    for _ in range(10):
        try:
            response = requests.get(f"http://localhost:{port}")
            if response.status_code == 200:
                flag = True
                break
        except Exception as e:
            time.sleep(5)
    if not flag:
        raise HTTPException(status_code=500, detail="The application did not start successfully")
    
    # Send the submission to the application
    response_json = response.json()

    # Stop the container and remove the volume
    docker.compose.down(volumes=True, quiet=True)
    if os.path.exists(destination_dir):
        shutil.rmtree(destination_dir)

    return {"message": "Submission created", "port": port, "response": response_json}
    # return {"message": "Submission created"}

# uvicorn app.main:app --port 8080