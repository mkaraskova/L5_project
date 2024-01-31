import requests
import logging
import json
import os
import sys
import time
import cv2
from fer import FER
from PIL import Image
from plyer import notification
import pystray
import threading
from queue import Queue


moods_queue = Queue()
running = True

emotion_messages = {
    "titles": {
        "sad": "Uh-Oh! Sadness Detected...",
        "happy": "Hooray! Pure Happiness Detected!",
        "neutral": "Chillin' Like a Villain: Neutral Mood Detected️",
        "surprise": "Hold on to Your Hat! Surprise Mood Detected!",
        "angry": "Whoa, Take a Breath! Anger Detected...",
        "fear": "Eek! Fear Mode Activated..."
    },
    "messages": {
        "sad": "Chin up, buttercup! A rainbow follows the rain.",
        "happy": "Smile wide! Your happiness is contagious.",
        "neutral": "Staying calm and collected, like a zen master.️",
        "surprise": "Guess what? Life just threw you a surprise party!",
        "angry": "Take a deep breath and count to ten. Anger doesn't solve anything.",
        "fear": "Facing fears makes you stronger. You're braver than you think!"
    }
}


def send_to_server(user_id, emotion, confidence):
    mood = {
        'userId': user_id,
        'mood': emotion,
        'confidence': confidence
    }
    moods_queue.put(mood)


def send_moods_to_server_thread(server):
    s = requests.Session()

    def fetch_csrf_token(server_url):
        while True:
            try:
                response = s.get(server_url)
                if response.status_code == 200:
                    return response.json()['csrf_token']
            except requests.exceptions.RequestException as e:
                logging.error(f"Network error when fetching CSRF token: {str(e)}")
                time.sleep(5)  # wait for 5 seconds before retrying

    while running:
        if not moods_queue.empty():
            mood = moods_queue.get()
            csrf_server = server + '/get-csrf-token'
            token = fetch_csrf_token(csrf_server)

            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            }

            mood_server = server + '/mood'

            for i in range(5):
                try:
                    response = s.post(mood_server, json=mood, headers=headers)
                    if response.status_code == 200:
                        logging.info(f"Mood data sent to the server: {response.text}")
                        moods_queue.task_done()
                        break
                    else:
                        logging.error(f"Failed to send mood data: {response.text}")
                        time.sleep(5)
                except requests.exceptions.RequestException as e:
                    logging.error(f"Network error: {str(e)}")
                    time.sleep(5)

            if i == 4:  # if it still fails after 5 attempts, then add it back to the queue
                moods_queue.put(mood)

        time.sleep(5)


def detect_emotion(user_id, detection_time, server):
    webcam_fps = 30
    frame_interval = detection_time * 60 * webcam_fps
    detector = FER(mtcnn=False)
    webcam = cv2.VideoCapture(0)
    frame_no = 1

    try:
        notification.notify(
            title='Hello',
            message='Starting mood detection now...',
            app_icon='icon.ico',
            timeout=10,
        )
    except Exception:
        notification.notify(
            title='Hello',
            message='Starting mood detection now...',
            timeout=10,
        )

    while running:
        ret, frame = webcam.read()

        if not ret:
            logging.error('detect_emotion: error reading in frames')
            break

        if frame_no % frame_interval == 0:
            faces = detector.detect_emotions(frame)
            while not faces:
                time.sleep(1)
                ret, frame = webcam.read()
                if not ret:
                    logging.error('detect_emotion: error reading in frames')
                    break
                faces = detector.detect_emotions(frame)

            face = faces[0]
            emotion = max(face["emotions"], key=face["emotions"].get)
            score = face["emotions"][emotion]
            logging.info(f"Mood detected: {emotion} with score: {score}")
            try:
                notification.notify(
                    title=emotion_messages['titles'][emotion],
                    message=emotion_messages['messages'][emotion],
                    app_icon='icon.ico',
                    timeout=20
                )
            except Exception:
                notification.notify(
                    title=emotion_messages['titles'][emotion],
                    message=emotion_messages['messages'][emotion],
                    timeout=20
                )
            send_to_server(user_id, emotion, score)
        frame_no += 1

    webcam.release()


def quit_program(icon, item):
    global running
    running = False
    icon.stop()


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))

    settings_path = os.path.join(script_dir, 'settings.json')
    with open(settings_path, 'r') as file:
        settings = json.load(file)

    user_id = settings['userId']
    server = settings.get('server') or 'http://localhost:4000'
    detection_time = settings['detection_time']

    image = Image.open("icon.ico")
    icon = pystray.Icon("eMood", image, "eMood",
                        menu=pystray.Menu(pystray.MenuItem('Stop mood monitoring', quit_program)))
    icon_thread = threading.Thread(target=icon.run)
    icon_thread.start()

    server_communication_thread = threading.Thread(target=send_moods_to_server_thread, args=(server,))
    server_communication_thread.start()

    detect_emotion(user_id, detection_time, server)