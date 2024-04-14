import cv2
import time
from messaging_operations import TwilioOperations

class MotionDetection:
    def __init__(self):
        self.is_detecting = False
        self.last_message_time = 0
        self.messaging_api = TwilioOperations()

    def start_motion_detection(self, stream_source, username, phone_number, stream_option, stream_link_entry, save_alert_data, gridfs):
        self.is_detecting = True 
        bg_sub = cv2.createBackgroundSubtractorMOG2(detectShadows=True, varThreshold=100, history=2000)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

        def is_person_present(frame, threshold=1100):
            fg_mask = bg_sub.apply(frame)
            _, fg_mask = cv2.threshold(fg_mask, 250, 255, cv2.THRESH_BINARY)
            fg_mask = cv2.dilate(fg_mask, kernel, iterations=4)
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours and cv2.contourArea(max(contours, key=cv2.contourArea)) > threshold:
                cnt = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(cnt)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, 'Person Detected', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1, cv2.LINE_AA)
                return True, frame
            else:
                return False, frame

        def motion_detection():
            cap = cv2.VideoCapture(stream_source)
            if not cap.isOpened():
                print("Error: Unable to open stream source.")
                self.is_detecting = False
                return

            while self.is_detecting: 
                ret, frame = cap.read()
                if not ret:
                    break

                new_width, new_height = 640, 480
                frame = cv2.resize(frame, (new_width, new_height))
                detected, annotated_image = is_person_present(frame)

                cv2.imshow("Motion Detection", annotated_image)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

                current_time = time.time()
                if detected and current_time - self.last_message_time > 120:
                    try:
                        self.messaging_api.send_message("Alert: Person detected!", phone_number)
                        self.last_message_time = current_time

                        _, image_bytes = cv2.imencode('.png', frame)
                        image_id = gridfs.put(image_bytes.tobytes(), filename=f"motion_detection_{time.strftime('%Y%m%d-%H%M%S')}.png")

                        save_alert_data(username, phone_number, stream_option, stream_link_entry, image_id)
                    except Exception as e:
                        print("Error sending message or saving screenshot:", e)

            cap.release()
            cv2.destroyAllWindows()

        motion_detection()
        self.is_detecting = False

    def stop_motion_detection(self):
        self.is_detecting = False

