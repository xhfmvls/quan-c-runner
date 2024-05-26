def delete_containers_and_images_by_name(image_name):
    client = docker.from_env()

    for container in client.containers.list(all=True):
        container_image_name = container.image.attrs['RepoTags'][0]
        if image_name in container_image_name:
            container.stop()
            container.remove(force=True)

    for image in client.images.list(all=True):
        image_tags = image.tags
        if f"{image_name}:latest" in image_tags:
            client.images.remove(image.id, force=True)

def build_image(port: int, image_tag: str):
    client = docker.from_env()
    try:
        image, build_logs = client.images.build(path=".", tag=image_tag, rm=True)

        container = client.containers.run(image_tag, detach=True, ports={'8080/tcp': port})
    except docker.errors.BuildError as e:
        error_message = {
            "error": "Build error",
            "message": list(e.build_log)
        }
        return False, error_message
    except docker.errors.APIError as e:
        error_message = {
            "error": "API error",
        }
        return False, error_message
    return True, build_logs

def run_tests_dev(test_data):
    port = 8080

    passed_test_case = []
    for idx, test in enumerate(test_data):
        checking_method = test['checking_method']
        url = test['url']
        url = url.replace("(port)", str(port))
        header = test['header']
        method = test['method']
        body = test['body']
        expected = test['expected']

        if checking_method(body, url, header, method, expected):
            passed_test_case.append(idx + 1)
    if len(passed_test_case) == 0:
        response_body = {
            "message": "No test cases passed, possible Error",
        }
    elif len(passed_test_case) != len(test_data):
        response_body = {
            "message": "Not all test cases passed, perhaps wrong logic or runtime error",
            "total_answer": len(test_data),
            "passed_test_case": passed_test_case,
        }
    else:
        response_body = {
            "message": "All test cases passed!",
            "total_answer": len(test_data),
            "passed_test_case": passed_test_case,
        }
    print(response_body)

def run_tests_final(test_data):
    time_start = time.time()
    port = generate_random_port()
    image_tag = generate_random_tag()
    build_success, data = build_image(port, image_tag)

    if(not build_success):
        print(data)
        return

    time.sleep(5)

    passed_test_case = []
    for idx, test in enumerate(test_data):
        checking_method = test['checking_method']
        url = test['url']
        url = url.replace("(port)", str(port))
        header = test['header']
        method = test['method']
        body = test['body']
        expected = test['expected']

        if checking_method(body, url, header, method, expected):
            passed_test_case.append(idx + 1)

    delete_containers_and_images_by_name(image_tag)
    end_time = time.time()

    if len(passed_test_case) == 0:
        response_body = {
            "message": "No test cases passed, possible Error",
            "execution_duration": f'{end_time - time_start:.2f}s'
        }
    elif len(passed_test_case) != len(test_data):
        response_body = {
            "message": "Not all test cases passed, perhaps wrong logic or runtime error",
            "total_answer": len(test_data),
            "passed_test_case": passed_test_case,
            "execution_duration": f'{end_time - time_start:.2f}s'
        }
    else:
        response_body = {
            "message": "All test cases passed!",
            "total_answer": len(test_data),
            "passed_test_case": passed_test_case,
            "execution_duration": f'{end_time - time_start:.2f}s'
        }
    print(response_body)


# @app.get("/compose_build")
# async def compose_build():
#     docker = DockerClient(compose_files=["../submission/testing-challange/docker-compose.yml"])

#     docker.compose.build()
#     docker.compose.up()

# async def print_numbers_task(numbers):
#     for number in numbers:
#         print(number)
#         await asyncio.sleep(0)  # Yield control to the event loop

# @app.get("/numbers")
# async def get_numbers():
#     numbers = list(range(1, 100001))  # Generate a large list to make the task more noticeable
#     # await print_numbers_task(numbers)  # Await the printing task to ensure it completes before returning << This is the key
#     asyncio.create_task(print_numbers_task(numbers))
#     return "Counting is finished and numbers are printed."

# uvicorn app.main:app --reload --port 8080