pip install fast-plate-ocr[onnx] --- pip install fast-plate-ocr[onnx-gpu]

## Dataset extractor
```
python dataset_extractor.py
```

### Dataset Validation
Before training the OCR model, it's strongly recommended to validate the dataset using the validate-dataset CLI command. This ensures image integrity, label consistency, and format compatibility with your plate config.

```
fast-plate-ocr validate-dataset --annotations-file ./data/train.csv --plate-config-file ./config/plate_config.yaml
```

## Training
### Requirements
pip install fast-plate-ocr[train]

### Training the OCR Model
From PowerShell:
```
set KERAS_BACKEND=tensorflow
```

```
fast-plate-ocr train --model-config-file ./models/cct_s_v1_model_config.yaml --plate-config-file ./config/plate_config.yaml --annotations train.csv --val-annotations val.csv --epochs 150 --batch-size 64 --output-dir ./trained_models
```

### Validating a Trained OCR Model
fast-plate-ocr valid --model ./trained_models/2026-03-08_14-18-10/last.keras --plate-config-file ./config/plate_config.yaml --annotations ./data/val.csv


### Exporting a Trained OCR Model
- Export to ONNX

fast-plate-ocr export --model trained_models/2026-03-08_14-18-10/last.keras --plate-config-file config/plate_config.yaml --format onnx --save-dir ./trained_models


- Export to TFLite

fast-plate-ocr export --model trained_models/2026-03-07_15-42-06/last.keras --plate-config-file ./config/plate_config.yaml --format tflite --save-dir ./trained_models

- Export to CoreML

fast-plate-ocr export --model trained_models/2026-03-07_15-42-06/last.keras --plate-config-file ./config/plate_config.yaml --format coreml --save-dir ./trained_models

En caso de error, ejecutar el script onnx_exporter como sigue:
python onnx_exporter.py

Visualizar predicciones
fast-plate-ocr visualize-predictions --model trained_models/2026-03-07_15-42-06/last.keras --img-dir 140x70_dataset/ags/ --plate-config-file plate_config.yaml
