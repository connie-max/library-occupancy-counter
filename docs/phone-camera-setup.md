# Phone Camera Setup Guide

## 1. Purpose
This guide explains how to connect a phone camera to the Library Occupancy Counter project so the camera stream can be accessed by the application.

## 2. Requirements
- A smartphone with a camera
- A phone camera streaming application
- A computer running the Library Occupancy Counter project
- VS Code and Python
- Both the phone and computer connected to the same Wi-Fi network
- The Python `requests` library

## 3. Phone Camera Setup
1. Connect the phone and computer to the same Wi-Fi network.
2. Open the camera streaming application on the phone.
3. Start the camera stream.
4. Find the video stream URL provided by the application.
5. Make sure the computer can access the phone's camera stream.

## 4. Configure the Camera URL
Open `test_camera.py` in the project folder.

Update the `camera_url` variable with the video stream URL provided by the phone camera application.

Example:

```python
camera_url = "http://PHONE_IP:PORT/video"
```

Replace `PHONE_IP` and `PORT` with the actual values provided by the application. The correct stream path may differ depending on the application.

## 5. Test the Connection
1. Open the project folder in VS Code.
2. Open the terminal.
3. Run the camera test script:

```bash
python test_camera.py
```

4. Check the terminal output.
5. If the stream is reachable, the script should report that the camera stream is reachable. Otherwise, check the URL, Wi-Fi connection, and camera streaming application.

## 6. Troubleshooting
- **Connection error:** Confirm that the phone and computer are connected to the same network.
- **Timeout:** Check whether the phone camera stream is running and accessible.
- **Incorrect URL:** Verify the IP address, port, and stream path.
- **Missing requests library:** Install it using `pip install requests`.

## 7. Notes
The phone camera application must support network streaming. The exact setup and stream URL depend on the application being used.