import json
import os
import time
import cv2
import logging
from fer import FER
import requests


def send_to_server(user_id, server_url, emotion, confidence):
    data = {
        'userId': user_id,
        'mood': emotion,
        'confidence': confidence
    }
    response = requests.post(server_url, json=data)
    logging.info(f"Mood data sent to the server: {response.text}")


def detect_emotion(user_id, detection_time, server):
    webcam_fps = 30
    frame_interval = detection_time * 60 * webcam_fps

    detector = FER(mtcnn=False)
    webcam = cv2.VideoCapture(0)
    frame_no = 0

    logging.info(f"Starting mood detection now...")
    while True:
        ret, frame = webcam.read()
        if not ret:
            logging.error('detect_emotion: error reading in frames')
            break
        frame_no += 1

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
            send_to_server(user_id, server, emotion, score)

    webcam.release()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, 'settings.json')
    with open(settings_path, 'r') as file:
        settings = json.load(file)
    user_id = settings['userId']
    server = settings['server']
    detection_time = settings['detection_time']
    detect_emotion(user_id, detection_time, server)
