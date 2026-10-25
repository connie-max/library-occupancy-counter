import requests

camera_url = "http://192.168.0.104:8080/video"

try:
    response = requests.get(
        camera_url,
        stream=True,
        timeout=5
    )

    if response.status_code == 200:
        print("Camera stream is reachable.")
    else:
        print("Camera returned:", response.status_code)

    response.close()

except requests.RequestException as error:
    print("Could not connect to the camera:", error)