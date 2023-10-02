import cv2
import logging
from fer import FER


def detect_emotion():
    detector = FER(mtcnn=False)  # initialize with MTCNN network
    webcam = cv2.VideoCapture(1)  # open 2nd webcam

    frame_no = 0
    emotion_text = None
    while True:
        frame_no += 1
        ret, frame = webcam.read()
        if not ret:
            logging.error(f'detect_emotion: error reading in frames')
            break
        if frame_no % 20 == 0:
            faces = detector.detect_emotions(frame)
            if faces:
                face = faces[0]
                (top, right, bottom, left) = face["box"]
                emotion = max(face["emotions"], key=face["emotions"].get)
                score = face["emotions"][emotion]

                emotion_text = f'{emotion}: {score:.2f}'

        if emotion_text:
            textbox, baseline = cv2.getTextSize(emotion_text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
            text_x = (frame.shape[1] - textbox[0]) // 2  # center the text
            text_y = frame.shape[0] - 5  # place the text at the bottom of the frame
            cv2.putText(frame, emotion_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow("Emotion Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    webcam.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    detect_emotion()


