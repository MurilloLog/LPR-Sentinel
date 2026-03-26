import cv2
import numpy as np
import onnxruntime as ort
import time
import imutils

# 1. Cargar el modelo ONNX
session = ort.InferenceSession("models/best.onnx")

# 2. Preprocesar imagen
def prepare_input(img_path):
    img = cv2.imread(img_path)
    original_img = img.copy()
    img_height, img_width = img.shape[:2]

    img = cv2.resize(img, (640, 640))
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    return np.expand_dims(img, axis=0), original_img, img_width, img_height

# 3. Postprocesar las salidas de YOLO
def postprocess(outputs, original_img, img_width, img_height, conf_threshold=0.7):
    """
    Postprocesa las salidas del modelo YOLO ONNX
    Formato de salida esperado: [batch, 84, 8400] donde 84 = 4 (bbox) + 80 (clases)
    """
    # Obtener las salidas del modelo
    output = outputs[0]  # [1, 84, 8400]
    output = output[0]   # [84, 8400]
    
    # Transponer para tener [8400, 84]
    output = output.T
    
    # Obtener las coordenadas de las cajas (x, y, w, h) en formato center
    boxes = output[:, :4]
    # Obtener las probabilidades de clase
    class_probs = output[:, 4:]
    
    # Obtener la clase con mayor probabilidad y su confianza
    class_ids = np.argmax(class_probs, axis=1)
    confidences = np.max(class_probs, axis=1)
    
    # Filtrar por umbral de confianza
    mask = confidences > conf_threshold
    boxes = boxes[mask]
    class_ids = class_ids[mask]
    confidences = confidences[mask]
    
    # Convertir de [x_center, y_center, width, height] a [x1, y1, x2, y2]
    x_center = boxes[:, 0]
    y_center = boxes[:, 1]
    width = boxes[:, 2]
    height = boxes[:, 3]
    
    # Escalar a las dimensiones originales de la imagen
    scale_x = img_width / 640.0
    scale_y = img_height / 640.0
    
    x1 = (x_center - width / 2) * scale_x
    y1 = (y_center - height / 2) * scale_y
    x2 = (x_center + width / 2) * scale_x
    y2 = (y_center + height / 2) * scale_y
    
    # Aplicar Non-Maximum Suppression (NMS)
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1).astype(np.int32)
    
    # NMS manual
    indices = cv2.dnn.NMSBoxes(
        boxes_xyxy.tolist(), 
        confidences.tolist(), 
        conf_threshold, 
        nms_threshold=0.45
    )
    
    if len(indices) > 0:
        indices = indices.flatten()
        boxes_xyxy = boxes_xyxy[indices]
        confidences = confidences[indices]
        class_ids = class_ids[indices]
    
    return boxes_xyxy, confidences, class_ids

# 3. Benchmark
input_name = session.get_inputs()[0].name
input_data, original_img, img_width, img_height = prepare_input("./inputs/test4.jpg")

start = time.time()
outputs = session.run(None, {input_name: input_data})
end = time.time()

print(f"Inferencia ONNX exitosa. Tiempo: {end - start:.4f}s")

# 5. Postprocesar resultados
boxes, confidences, class_ids = postprocess(outputs, original_img, img_width, img_height)

# 6. Procesar detecciones (clase 0 = placas)
detections_found = False
for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
    # Verificar si es la clase 0 (placas)
    if class_id == 0 and conf > 0.7:  # conf > 70% (0.7)
        x1, y1, x2, y2 = box
        
        # Extraer y guardar la placa con margen
        y1_margin = max(0, y1 - 20)
        y2_margin = min(original_img.shape[0], y2 + 20)
        x1_margin = max(0, x1 - 20)
        x2_margin = min(original_img.shape[1], x2 + 20)
        
        plate_image = original_img[y1_margin:y2_margin, x1_margin:x2_margin]
        cv2.imwrite("outputs/ROI.jpg", plate_image)
        
        # Dibujar rectángulo en la imagen original
        cv2.rectangle(original_img, (x1, y1), (x2, y2), (0, 255, 0), 5)
        
        # Agregar texto con la confianza
        label = f"Placa: {conf:.2f}"
        cv2.putText(original_img, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        print(f"Placa detectada con confianza: {conf:.2f}")
        detections_found = True

if not detections_found:
    print("No se detectaron placas con confianza > 70%")

# 7. Redimensionar y guardar resultado final
final_image = imutils.resize(original_img, width=720)
cv2.imwrite("outputs/FullROI.jpg", final_image)