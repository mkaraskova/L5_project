import os

import cv2
import logging
import threading
from fer import FER
from pymongo import MongoClient
import datetime

# Initialize MongoDB client and collections
client = MongoClient(os.getenv('MONGO_DB'))
db = client["eMood"]
moods = db["Moods"]


def send_to_mongodb(emotion):
    current_time = datetime.datetime.now()
    with open('eMood_app/eMood_detector/userid.txt', 'r') as file:
        user_id = file.readline().strip()
    data = {
        'userId': user_id,
        'timestamp': current_time,
        'mood': emotion
    }
    moods.insert_one(data)
    logging.info(f"Mood data sent to MongoDB")


def detect_emotion():
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
            if emotion:
                threading.Thread(target=send_to_mongodb, args=(emotion,)).start()
                emotions = {}  # Reset emotions after sending to MongoDB

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    detect_emotion()
