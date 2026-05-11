"""
LPR-Sentinel: A High-Speed Neural Vision System for Mexican Licence Plate Recognition
Concurso de Programacion 'Hola Mundo', mayo de 2026.
Autor: Gustavo Adolfo Murillo Gutierrez

Descripcion: Este programa implementa un pipeline de vision por computadora que:
1. Detecta placas vehiculares en una imagen usando YOLOv11s (ONNX)
2. Extrae la region de interes (ROI) de la placa detectada
3. Realiza OCR sobre la ROI usando una adaptacion de FastPlateOCR (ONNX)
4. Consulta una base de datos SQLite para obtener informacion asociada a la placa

Uso: Para ejecutarse, se debera invocar este script desde la interfaz de comandos y
especificar el directorio de la imagen a procesar de la siguiente manera:
    $ python main.py --image ./ruta/a/imagen.jpg

Podra encontrar algunas imagenes dentro del directorio /inputs.
"""

import os
import sys
import argparse
import sqlite3
import cv2
import numpy as np
import yaml
import imutils
import pandas as pd
import onnxruntime as ort
import traceback
from pathlib import Path
from typing import Tuple, Dict, List, Optional

#region Variables
# Ubicacion de los modelos y sus configuraciones
#DETECTOR_ONNX_MODEL_PATH = "./models/MLP_Detector.onnx"
DETECTOR_ONNX_MODEL_PATH = "./models/MLP_Detector_v8n.onnx"
OCR_ONNX_MODEL_PATH = "./models/MLP_Recognizer.onnx"
OCR_CONFIG_PATH = "./config/plate_config.yaml"
DATABASE_PATH = "./database/MLPR.db"
CSV_METADATA_PATH = "./database/license_plates_metadata.csv"

# Parametrizacion del detector
DETECTOR_IMG_SIZE = 640 # Dimension de la imagen esperada por el detector
DETECTOR_CONF_THRESHOLD = 0.7 # Umbral de confianza para considerar una deteccion exitosa
DETECTOR_NMS_THRESHOLD = 0.45 # Umbral Non-Maximum Suppression (NMS)
DETECTOR_PLATE_CLASS_ID = 0 # ID de la clase para placa vehicular
ROI_MARGIN = 5 # Margen adicional en la extraccion del ROI
#endregion

#region Clase principal
class LPRSentinel:
    """
    Procesamiento de placas vehiculares mexicanas
    
    Esta clase integra la deteccion, el reconocimiento y la consulta a base de datos.
    """
    
    def __init__(
        self,
        detector_model_path: str = DETECTOR_ONNX_MODEL_PATH,
        ocr_model_path: str = OCR_ONNX_MODEL_PATH,
        ocr_config_path: str = OCR_CONFIG_PATH,
        database_path: str = DATABASE_PATH,
        csv_metadata_path: str = CSV_METADATA_PATH,
        output_dir: str = "outputs"
    ):
        
        self.detector_model_path = detector_model_path
        self.ocr_model_path = ocr_model_path
        self.ocr_config_path = ocr_config_path
        self.database_path = database_path
        self.csv_metadata_path = csv_metadata_path
        self.output_dir = output_dir
        
        # Creacion del directorio 'outputs' para guardar resultados
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Inicializacion de componentes
        self._load_detector_model()
        self._load_ocr_config()
        self._load_ocr_model()
        self._initialize_database()
        
    #region Inicializacion
    def _load_detector_model(self) -> None:
        """Carga el modelo YOLOv11s en su formato ONNX para la deteccion de placas."""
        try:
            self.detector_session = ort.InferenceSession(self.detector_model_path)
            self.detector_input_name = self.detector_session.get_inputs()[0].name
            #print(f"Detector cargado: {self.detector_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar el detector ONNX: {e}")
    
    def _load_ocr_config(self) -> None:
        """Carga la configuracion del modelo OCR."""
        try:
            with open(self.ocr_config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.ocr_config = {
                'max_plate_slots': config.get('max_plate_slots', 9),
                'alphabet': config.get('alphabet', '0123456789ABCDEFGHJKLMNPRSTUVWXYZ-'),
                'pad_char': config.get('pad_char', '-'),
                'img_height': config.get('img_height', 70),
                'img_width': config.get('img_width', 140),
                'keep_aspect_ratio': config.get('keep_aspect_ratio', True),
                'interpolation': config.get('interpolation', 'linear'),
                'image_color_mode': config.get('image_color_mode', 'grayscale')
            }
            self.ocr_alphabet = self.ocr_config['alphabet']
            #print(f"Configuracion OCR cargada: {self.ocr_config_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar la configuracion del modelo OCR: {e}")
    
    def _load_ocr_model(self) -> None:
        """Carga el modelo OCR en formato ONNX para el reconocimiento de los caracteres."""
        try:
            self.ocr_session = ort.InferenceSession(self.ocr_model_path)
            self.ocr_input_name = self.ocr_session.get_inputs()[0].name
            self.ocr_output_name = self.ocr_session.get_outputs()[0].name
            #print(f"Modelo OCR cargado: {self.ocr_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar el modelo OCR: {e}")
    
    def _initialize_database(self) -> None:
        """Inicializa la base de datos SQLite, creando la tabla de ser necesario."""
        try:
            # Verificar si la base de datos existe
            db_exists = Path(self.database_path).exists()
            
            # Conectar a la base de datos
            self.conn = sqlite3.connect(self.database_path)
            
            # Si la base de datos no existe o la tabla esta vacia, intentar generarla desde los metadatos CSV
            if not db_exists or self._is_table_empty():
                if Path(self.csv_metadata_path).exists():
                    self._load_csv_to_database()
                else:
                    print(f"No se encontro archivo CSV: {self.csv_metadata_path}")
                    print("La base de datos estara vacia inicialmente.")
            #else:
                #print(f"Base de datos existente: {self.database_path}")
                
        except Exception as e:
            raise RuntimeError(f"Error al cargar la base de datos: {e}")
    
    def _is_table_empty(self) -> bool:
        """Verifica si la tabla 'Registros' esta vacia."""
        try:
            query = "SELECT COUNT(*) FROM Registros"
            cursor = self.conn.execute(query)
            count = cursor.fetchone()[0]
            return count == 0
        except sqlite3.OperationalError:
            # La tabla no existe
            return True
    
    def _load_csv_to_database(self) -> None:
        """Carga los datos del CSV a la base de datos SQLite."""
        try:
            df = pd.read_csv(self.csv_metadata_path)
            df.to_sql('Registros', self.conn, if_exists='replace', index=False)
            #print(f"Datos cargados desde CSV: {len(df)} registros en tabla 'Registros'")
        except Exception as e:
            print(f"Error al cargar CSV: {e}")
            # Crear tabla vacia
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Registros (
                    Matricula TEXT PRIMARY KEY,
                    Estado TEXT,
                    Marca/Modelo TEXT,
                    Color TEXT,
                    Estatus TEXT,
                    Propietario TEXT
                    FechaRegistro TEXT,
                    Filename TEXT                    
                )
            """)
            print("Tabla 'Registros' creada (vacia)")
    
    #region Preprocesamiento
    def _prepare_detector_input(self, img_path: str) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """
        Prepara la imagen para el detector.
        
        Parametros:
        img_path : str
            Ruta a la imagen de entrada.
        
        Retorna:
        tuple
            (input_data, original_img, img_width, img_height)
        """
        img = cv2.imread(img_path)
        if img is None:
            raise FileNotFoundError(f"No se pudo cargar la imagen: {img_path}")
        
        original_img = img.copy()
        img_height, img_width = img.shape[:2]
        
        # Redimensionar a 640x640
        img = cv2.resize(img, (DETECTOR_IMG_SIZE, DETECTOR_IMG_SIZE))
        img = img.astype(np.float32) / 255.0
        img = np.transpose(img, (2, 0, 1))
        input_data = np.expand_dims(img, axis=0)
        
        return input_data, original_img, img_width, img_height
    
    def _postprocess_detections(
        self,
        outputs: List[np.ndarray],
        original_img: np.ndarray,
        img_width: int,
        img_height: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Postprocesa las salidas del detector.
        
        Parametros:
        outputs : list
            Salidas del modelo ONNX.
        original_img : np.ndarray
            Imagen original para escalado.
        img_width : int
            Ancho original de la imagen.
        img_height : int
            Alto original de la imagen.
        
        Retorna:
        tuple
            (boxes, confidences, class_ids)
        """
        output = outputs[0][0]  # [84, 8400]
        output = output.T  # [8400, 84]
        
        boxes = output[:, :4]
        class_probs = output[:, 4:]
        
        class_ids = np.argmax(class_probs, axis=1)
        confidences = np.max(class_probs, axis=1)
        
        # Filtrar por umbral de confianza
        mask = confidences > DETECTOR_CONF_THRESHOLD
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]
        
        # Convertir de [x_center, y_center, width, height] a [x1, y1, x2, y2]
        x_center = boxes[:, 0]
        y_center = boxes[:, 1]
        width = boxes[:, 2]
        height = boxes[:, 3]
        
        # Escalar a dimensiones originales
        scale_x = img_width / DETECTOR_IMG_SIZE
        scale_y = img_height / DETECTOR_IMG_SIZE
        
        x1 = (x_center - width / 2) * scale_x
        y1 = (y_center - height / 2) * scale_y
        x2 = (x_center + width / 2) * scale_x
        y2 = (y_center + height / 2) * scale_y
        
        boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1).astype(np.int32)
        
        # Aplicar NMS
        indices = cv2.dnn.NMSBoxes(
            boxes_xyxy.tolist(),
            confidences.tolist(),
            DETECTOR_CONF_THRESHOLD,
            DETECTOR_NMS_THRESHOLD
        )
        
        if len(indices) > 0:
            indices = indices.flatten()
            boxes_xyxy = boxes_xyxy[indices]
            confidences = confidences[indices]
            class_ids = class_ids[indices]
        
        return boxes_xyxy, confidences, class_ids
    
    def _preprocess_ocr_image(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocesa la imagen para ingresar al reconocedor.
        
        Parametros:
        img : np.ndarray
            Imagen de la placa (ROI).
        
        Retorna:
        np.ndarray
            Imagen preprocesada con dimensiones (1, height, width, channels).
        """
        config = self.ocr_config
        
        # Convertir a escala de grises
        if config['image_color_mode'] == 'grayscale':
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        target_h = config['img_height']
        target_w = config['img_width']
        
        # Redimensionar manteniendo el aspect ratio
        if config['keep_aspect_ratio']:
            h, w = img.shape[:2]
            aspect = w / h
            
            if w / h > target_w / target_h:
                new_w = target_w
                new_h = int(target_w / aspect)
            else:
                new_h = target_h
                new_w = int(target_h * aspect)
            
            # Interpolacion
            interpolation = cv2.INTER_LINEAR if config['interpolation'] == 'linear' else cv2.INTER_CUBIC
            
            img_resized = cv2.resize(img, (new_w, new_h), interpolation=interpolation)
            
            # Crear canvas negro
            if config['image_color_mode'] == 'grayscale':
                canvas = np.zeros((target_h, target_w), dtype=np.float32)
            else:
                canvas = np.zeros((target_h, target_w, 3), dtype=np.float32)
            
            # Centrar la imagen
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = img_resized
            img_processed = canvas
        else:
            img_processed = cv2.resize(img, (target_w, target_h))
        
        # Convertir a float32 sin normalizar
        img_processed = img_processed.astype(np.float32)
        
        # Asegurar el formato de escala de grises
        if config['image_color_mode'] == 'grayscale' and len(img_processed.shape) == 2:
            img_processed = np.expand_dims(img_processed, axis=-1)
        
        # Agregar dimension
        img_processed = np.expand_dims(img_processed, axis=0)
        
        return img_processed
    
    def _decode_ocr_prediction(self, predictions: np.ndarray) -> Tuple[str, List[float]]:
        """
        Decodifica la salida del reconocedor a texto.
        
        Parametros:
        predictions : np.ndarray
            Predicciones del modelo con forma (batch, sequence, vocab_size).
        
        Retorna:
        tuple
            (plate_text, confidences)
        """
        # Aplicar softmax para filtrar mejor prediccion
        probs = predictions[0]
        exp_probs = np.exp(probs - np.max(probs, axis=-1, keepdims=True))
        softmax_probs = exp_probs / np.sum(exp_probs, axis=-1, keepdims=True)
        
        # Obtener indices con mayor probabilidad
        pred_indices = np.argmax(softmax_probs, axis=-1)
        
        chars = []
        confidences = []
        
        for idx, char_idx in enumerate(pred_indices):
            if char_idx < len(self.ocr_alphabet):
                char = self.ocr_alphabet[char_idx]
                prob = softmax_probs[idx][char_idx]
                chars.append(char)
                confidences.append(prob)
        
        plate_text = "".join(chars)
        return plate_text, confidences
    
    #region Consultas BD
    def _query_database(self, plate: str) -> Optional[Dict]:
        """
        Consulta la base de datos para obtener informacion de la placa.
        
        Parametros:
        plate : str
            Matricula a consultar.
        
        Retorna:
        dict or None
            Diccionario con los datos de la placa o None si no existe.
        """
        try:
            query = "SELECT * FROM Registros WHERE Matricula = ?"
            cursor = self.conn.execute(query, (plate,))
            row = cursor.fetchone()
            
            if row:
                # Obtener nombres de columnas
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except sqlite3.Error as e:
            print(f"Error en consulta a base de datos: {e}")
            return None

    #region Pipeline
    def process_image(self, image_path: str) -> Dict:
        """
        Procesa una imagen completa.
        
        Parametros:
        image_path : str
            Ruta a la imagen de entrada.
        
        Retorna:
        dict
            Diccionario con los resultados de la inferencia.
        """
        results = {
            'success': False,
            'image_path': image_path,
            'detection': None,
            'roi_path': None,
            'plate_text': None,
            'ocr_confidence': None,
            'database_record': None,
            'error': None
        }
        
        try:
            # Preparacion del detector de placas
            input_data, original_img, img_width, img_height = self._prepare_detector_input(image_path)
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, original_img, img_width, img_height
            )
            
            # Buscar posibles placas en la imagen (clase 0)
            plate_box = None
            plate_confidence = None
            
            for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if class_id == DETECTOR_PLATE_CLASS_ID:
                    plate_box = box
                    plate_confidence = conf
                    break
            
            if plate_box is None:
                #print("No se detectaron placas vehiculares en la imagen")
                results['error'] = "No se detectaron placas"
                return results
            
            x1, y1, x2, y2 = plate_box
            #print(f"Placa detectada con confianza: {plate_confidence:.4f}")
            #print(f"Coordenadas: ({x1}, {y1}) -> ({x2}, {y2})")
            
            results['detection'] = {
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(plate_confidence)
            }
            
            # Extraccion de ROI
            # Agregar margen de compensacion
            y1_margin = max(0, y1 - ROI_MARGIN)
            y2_margin = min(original_img.shape[0], y2 + ROI_MARGIN)
            x1_margin = max(0, x1 - ROI_MARGIN)
            x2_margin = min(original_img.shape[1], x2 + ROI_MARGIN)
            
            plate_roi = original_img[y1_margin:y2_margin, x1_margin:x2_margin]
            
            # Guardar ROI
            roi_filename = f"roi_{Path(image_path).stem}.jpg"
            roi_path = os.path.join(self.output_dir, roi_filename)
            cv2.imwrite(roi_path, plate_roi)
            results['roi_path'] = roi_path
            
            # Dibujar rectangulo en imagen original (para depuracion)
            cv2.rectangle(original_img, (x1, y1), (x2, y2), (0, 255, 0), 5)
            label = f"Placa: {plate_confidence:.2f}"
            cv2.putText(original_img, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Guardar imagen con deteccion
            final_image = imutils.resize(original_img, width=720)
            full_path = os.path.join(self.output_dir, f"full_{Path(image_path).stem}.jpg")
            cv2.imwrite(full_path, final_image)
            #print(f"Imagen con deteccion guardada en: {full_path}")
            
            # OCR sobre la ROI
            ocr_input = self._preprocess_ocr_image(plate_roi)
            predictions = self.ocr_session.run(
                [self.ocr_output_name],
                {self.ocr_input_name: ocr_input}
            )[0]
            
            plate_text, ocr_confidences = self._decode_ocr_prediction(predictions)
            mean_confidence = np.mean(ocr_confidences) if ocr_confidences else 0
            
            #print(f"Placa reconocida: {plate_text}")
            #print(f"Confianza promedio: {mean_confidence:.4f}")
            #print(f"Confianza por caracter: {[f'{c}:{conf:.4f}' for c, conf in zip(plate_text, ocr_confidences)]}")
            
            results['plate_text'] = plate_text
            results['ocr_confidence'] = mean_confidence
            
            # Consulta a base de datos
            database_record = self._query_database(plate_text)
            
            if database_record:
                #print("Registro encontrado:")
                for key, value in database_record.items():
                    print(f"   {key}: {value}")
                results['database_record'] = database_record
            else:
                #print(f"No se encontro registro para esta placa: {plate_text}")
                results['database_record'] = None
            
            results['success'] = True
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            print(f"\nError en el pipeline: {e}")
            
            traceback.print_exc()
            return results
    
    def __del__(self):
        """Cierra la conexion a la base de datos al destruir el objeto."""
        if hasattr(self, 'conn'):
            self.conn.close()

#region main()
def main():
    """
    Punto de entrada principal del script.
    """
    parser = argparse.ArgumentParser(
        description='Deteccion y reconocimiento de placas vehiculares mexicanas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Ejemplos de uso:
            python main.py --image ./input/diurna/Test51.png
            python main.py --image ./input/nocturna/Test1.png
        """
    )
    
    parser.add_argument(
        '--image',
        type=str,
        required=True,
        help='Ruta a la imagen de entrada'
    )
    
    args = parser.parse_args()
    
    # Verificar que la imagen existe
    if not Path(args.image).exists():
        print(f"Error: No se encontro la imagen: {args.image}")
        sys.exit(1)
    
    # Crear pipeline y procesar
    try:
        pipeline = LPRSentinel()
        
        results = pipeline.process_image(args.image)
        
        # Mostrar resumen final para demo
        if not(results['success']):
            print(f"Matricula no detectada. Intente nuevamente desde otro angulo")
            
        if not(results['database_record']):
            print(f"Datos asociados: No encontrados")
        
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()