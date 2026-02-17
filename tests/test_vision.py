import cv2
import ultralytics

print(f"Version de OpenCV: {cv2.__version__}")
print(f"Version de Ultralytics: {ultralytics.__version__}")

# Video capturing
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: No se pudo acceder a la camara.")
else:
    print("Camara detectada correctamente.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: No se pudo leer el frame de la camara.") 
            break 
        # Show video 
        cv2.imshow("Video en vivo", frame) 
        
        # Press key 'q' to exit 
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Closing all
    cap.release()
    cv2.destroyAllWindows()