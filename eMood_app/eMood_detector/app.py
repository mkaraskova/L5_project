import json
import logging
import os
import sys
import time

import cv2
import requests
from fer import FER
from plyer import notification

emotion_messages = {
    "titles": {"sad": "Uh-Oh! Sadness Detected...",
               "happy": "Hooray! Pure Happiness Detected!",
               "neutral": "Chillin' Like a Villain: Neutral Mood Detected️",
               "surprise": "Hold on to Your Hat! Surprise Mood Detected!",
               "angry": "Whoa, Take a Breath! Anger Detected...",
               "fear": "Eek! Fear Mode Activated..."},
    "messages": {"sad": "Chin up, buttercup! A rainbow follows the rain.",
                 "happy": "Smile wide! Your happiness is contagious.",
                 "neutral": "Staying calm and collected, like a zen master. ️",
                 "surprise": "Guess what? Life just threw you a surprise party!",
                 "angry": "Take a deep breath and count to ten. Anger doesn't solve anything.",
                 "fear": "Facing fears makes you stronger. You're braver than you think!"}

}

s = requests.Session()
server_status = False
moods = []


def check_server(server):
    global server_status
    try:
        response = s.get(server)
        if response.status_code == 200:
            server_status = True
        else:
            server_status = False
    except requests.exceptions.ConnectionError:
        server_status = False
    return server_status


def fetch_csrf_token(server_url):
    response = s.get(server_url)
    if response.status_code == 200:
        return response.json()['csrf_token']
    else:
        return None


def send_to_server(user_id, server, emotion, confidence):
    global server_status
    global moods

    if check_server(server):
        moods.append({
            'userId': user_id,
            'mood': emotion,
            'confidence': confidence
        })

        for mood in moods:
            mood_server = server + '/mood'
            csrf_server = server + '/get-csrf-token'
            token = fetch_csrf_token(csrf_server)

            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': token}

            response = s.post(mood_server, json=mood, headers=headers)
            if response.status_code == 200:
                print(f"Mood data sent to the server: {response.text}")
                moods.remove(mood)
            else:
                print(f"Failed to send mood data: {response.text}")
                break
    else:
        moods.append({
            'userId': user_id,
            'mood': emotion,
            'confidence': confidence
        })


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
    while True:
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
            send_to_server(user_id, server, emotion, score)
        frame_no += 1

    webcam.release()


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
    detect_emotion(user_id, detection_time, server)
