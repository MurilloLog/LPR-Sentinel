from roboflow import Roboflow
from ultralytics import YOLO

rf = Roboflow(api_key="aYnmGP70Ofqcas4vynAq")
project = rf.workspace("licenseplate-s6fjf").project("license-plate-xmnzu")
version = project.version(1)
dataset = version.download("yolov11")
model = YOLO('yolo11s.pt')

data_path = "/content/license-plate-1/data.yaml"
results = model.train(data=data_path, epochs=50, imgsz=640)

custom_model = YOLO('/content/runs/detect/train/weights/best.pt')

res = custom_model("/content/license-plate-1/test/images")