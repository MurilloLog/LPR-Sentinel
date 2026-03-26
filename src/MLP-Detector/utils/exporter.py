from ultralytics import YOLO
model = YOLO('best.pt')
model.export(format='onnx', imgsz=640) # Esto creara 'yolov9t.onnx'