import cv2
import logging
from fer import FER
import matplotlib.pyplot as plt
from statistics import mean


def detect_emotion():
    detector = FER(mtcnn=False)  # initialize with MTCNN network
    webcam = cv2.VideoCapture(1)  # open 2nd webcam

    frame_no = 0
    emotion_text = None
    emotions = {}
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

                # track emotions
                if emotion not in emotions:
                    emotions[emotion] = [score]
                else:
                    emotions[emotion].append(score)

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

    emotion_names = emotions.keys()
    emotion_frequencies = [len(values) for values in emotions.values()]
    emotion_averages = [mean(values) for values in emotions.values()]

    fig, axs = plt.subplots(2)

    # Plot emotion frequencies
    axs[0].bar(emotion_names, emotion_frequencies, color='r')
    axs[0].set_title('Emotion Frequencies')
    axs[0].set_ylabel('Frequencies')

    # Plot average intensities
    axs[1].bar(emotion_names, emotion_averages, color='b')
    axs[1].set_title('Average Intensities')
    axs[1].set_ylabel('Average Intensity')

    # Set common x-axis properties
    for ax in axs:
        ax.set_xticks(range(len(emotion_names)))
        ax.set_xticklabels(emotion_names, rotation=45)

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    detect_emotion()


