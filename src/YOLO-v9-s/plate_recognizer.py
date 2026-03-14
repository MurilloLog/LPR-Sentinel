from ultralytics import YOLO
import cv2
import imutils

image = cv2.imread("./inputs/test6.jpg")

model = YOLO("best.pt")

results = model(image)
print(results[0].boxes)

for result in results:
    index_plates = (result.boxes.cls == 0).nonzero(as_tuple=True)[0]
    for idx in index_plates:
        conf = result.boxes.conf[idx].item()
        if conf > 70:
            xyxy = result.boxes.xyxy[idx].squeeze().tolist()
            x1, y1 = int(xyxy[0]), int(xyxy[1])
            x2, y2 = int(xyxy[2]), int(xyxy[3])

            plate_image = image[y1-20:y2+20, x1-20:x2+20]
            cv2.imwrite("Placa.jpg", plate_image)
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 5)
            print("Placa detectada")

image = imutils.resize(image, width=720)
cv2.imwrite("Resultado.jpg", image)
