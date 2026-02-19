import cv2
import time
import os

print(f"OpenCV version: {cv2.__version__}")

# Global test images
os.makedirs("TestImages", exist_ok=True)

# Video capturing
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Camera not found")
else:
    print("Camera ok")

    for i in range(5):  # Capturing 5 frames
        ret, frame = cap.read()
        if not ret:
            print(f"Error capturing frame {i}")
            continue
        
        # Saving frame on global test images dir
        filename = f"TestImages/frame_{time.time()}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Frame {i+1} saved as: {filename}")
        
        # Delay between frames
        time.sleep(0.5)

    # Closing all
    cap.release()