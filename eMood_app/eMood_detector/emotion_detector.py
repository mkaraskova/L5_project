import json
import os
import sys
import cv2
import logging
import threading
from fer import FER
from pymongo import MongoClient
import datetime


def send_to_mongodb(user_id, mongo_connection, emotion):
    client = MongoClient(mongo_connection)
    db = client["eMood"]
    moods = db["Moods"]

    current_time = datetime.datetime.now()
    data = {
        'userId': user_id,
        'timestamp': current_time,
        'mood': emotion
    }
    moods.insert_one(data)
    logging.info(f"Mood data sent to MongoDB")


def detect_emotion(user_id, mongo_connection):
    detector = FER(mtcnn=False)
    webcam = cv2.VideoCapture(0)

    frame_no = 0
    emotions = {}
    while True:
        frame_no += 1
        ret, frame = webcam.read()
        if not ret:
            logging.error('detect_emotion: error reading in frames')
            break
        if frame_no % 20 == 0:
            faces = detector.detect_emotions(frame)
            if faces:
                face = faces[0]
                emotion = max(face["emotions"], key=face["emotions"].get)
                score = face["emotions"][emotion]

                # track emotions
                if emotion not in emotions:
                    emotions[emotion] = [score]
                else:
                    emotions[emotion].append(score)

        if frame_no % (20 * 60) == 0:  # Send data to MongoDB every minute if emotion detected
            if 'emotion' in locals():
                threading.Thread(target=send_to_mongodb, args=(user_id, mongo_connection, emotion)).start()
                emotions = {}  # Reset emotions after sending to MongoDB

    webcam.release()


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, 'settings.json')
    with open(settings_path, 'r') as file:
        settings = json.load(file)
    user_id = settings['userId']
    mongo_connection = settings['mongoConnection']
    detect_emotion(user_id, mongo_connection)
