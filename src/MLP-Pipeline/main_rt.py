"""
Deteccion y reconocimiento de placas vehiculares - Modo imagen, video y tiempo real

Este script implementa un pipeline de vision por computadora que:
1. Detecta placas vehiculares en una imagen, video o camara en tiempo real usando un modelo YOLO (ONNX)
2. Extrae la region de interes (ROI) de la placa detectada
3. Realiza OCR sobre la ROI usando un modelo de reconocimiento de texto (ONNX)
4. Consulta una base de datos SQLite para obtener informacion asociada a la placa

Uso:
    # Modo imagen
    python main.py --image ruta/a/imagen.jpg
    
    # Modo video (procesa video guardado)
    python main.py --video ruta/a/video.mp4 --output-video resultado.mp4
    
    # Modo tiempo real (camara)
    python main.py --camera --camera-id 0
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
from pathlib import Path
from typing import Tuple, Dict, List, Optional, Union
from datetime import datetime
import time
import signal

#region Variables
# Rutas de modelos y configuraciones
DETECTOR_MODEL_PATH = "../MLP-Detector/models/best.onnx" # Modelo YOLO para deteccion
OCR_MODEL_PATH = "../MLP-Recognizer/models/best.onnx" # Modelo OCR para reconocimiento
OCR_CONFIG_PATH = "../MLP-Recognizer/config/plate_config.yaml" # Configuracion del modelo OCR
DATABASE_PATH = "../MLP-Register/database/MLPR.db" # Ruta a la base de datos SQLite
CSV_METADATA_PATH = "../MLP-Generator/dataset/license_plates_metadata.csv" # CSV dataset

# Constantes del detector
DETECTOR_IMG_SIZE = 640 # Tamanio de entrada del detector
DETECTOR_CONF_THRESHOLD = 0.7 # Umbral de confianza para deteccion
DETECTOR_NMS_THRESHOLD = 0.45 # Umbral NMS
DETECTOR_PLATE_CLASS_ID = 0 # ID de clase para placa vehicular
ROI_MARGIN = 1 # Margen para extraer ROI

# Constantes para procesamiento de video
VIDEO_SKIP_FRAMES = 2  # Procesar cada N frames para mejorar rendimiento
DETECTION_COOLDOWN_FRAMES = 30  # Frames de espera antes de reprocesar misma placa
#endregion

#region Main class
class MexicanLicencePlateDetector:
    """
    Procesamiento de placas vehiculares mexicanas
    
    Esta clase integra deteccion, OCR y consulta a base de datos.
    Soporta procesamiento de imagenes, videos y camara en tiempo real.
    """
    
    def __init__(
        self,
        detector_model_path: str = DETECTOR_MODEL_PATH,
        ocr_model_path: str = OCR_MODEL_PATH,
        ocr_config_path: str = OCR_CONFIG_PATH,
        database_path: str = DATABASE_PATH,
        csv_metadata_path: str = CSV_METADATA_PATH,
        output_dir: str = "outputs"
    ):
        """
        Inicializa el pipeline con los modelos y configuraciones necesarias.
        
        Parametros
        ----------
        detector_model_path : str
            Ruta al modelo ONNX del detector YOLO.
        ocr_model_path : str
            Ruta al modelo ONNX del OCR.
        ocr_config_path : str
            Ruta al archivo YAML de configuracion del OCR.
        database_path : str
            Ruta a la base de datos SQLite.
        csv_metadata_path : str
            Ruta al archivo CSV para inicializar la base de datos (opcional).
        output_dir : str
            Directorio donde se guardaran los archivos de salida.
        """
        self.detector_model_path = detector_model_path
        self.ocr_model_path = ocr_model_path
        self.ocr_config_path = ocr_config_path
        self.database_path = database_path
        self.csv_metadata_path = csv_metadata_path
        self.output_dir = output_dir
        
        # Variables para procesamiento de video
        self.last_detected_plate = None
        self.last_detection_frame = 0
        self.frame_count = 0
        self.video_writer = None
        self.running = True
        
        # Crear directorio de salida si no existe
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        self._load_detector_model()
        self._load_ocr_config()
        self._load_ocr_model()
        self._initialize_database()
        
        # Configurar signal handler para cerrar gracefulmente
        signal.signal(signal.SIGINT, self._signal_handler)
        
    # Metodos de inicializacion
    def _load_detector_model(self) -> None:
        """Carga el modelo YOLO ONNX para deteccion de placas."""
        try:
            self.detector_session = ort.InferenceSession(self.detector_model_path)
            self.detector_input_name = self.detector_session.get_inputs()[0].name
            print(f"Detector cargado: {self.detector_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar detector ONNX: {e}")
    
    def _load_ocr_config(self) -> None:
        """Carga la configuracion del modelo OCR desde archivo YAML."""
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
            print(f"Configuracion OCR cargada: {self.ocr_config_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar configuracion OCR: {e}")
    
    def _load_ocr_model(self) -> None:
        """Carga el modelo OCR ONNX para reconocimiento de texto."""
        try:
            self.ocr_session = ort.InferenceSession(self.ocr_model_path)
            self.ocr_input_name = self.ocr_session.get_inputs()[0].name
            self.ocr_output_name = self.ocr_session.get_outputs()[0].name
            print(f"Modelo OCR cargado: {self.ocr_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error al cargar modelo OCR: {e}")
    
    def _initialize_database(self) -> None:
        """Inicializa la base de datos SQLite, creando la tabla si es necesario."""
        try:
            # Verificar si la base de datos existe
            db_exists = Path(self.database_path).exists()
            
            # Conectar a la base de datos
            self.conn = sqlite3.connect(self.database_path)
            
            # Si la base de datos no existe o la tabla esta vacia, intentar cargar desde CSV
            if not db_exists or self._is_table_empty():
                if Path(self.csv_metadata_path).exists():
                    self._load_csv_to_database()
                else:
                    print(f"No se encontro archivo CSV: {self.csv_metadata_path}")
                    print("La base de datos estara vacia inicialmente.")
            else:
                print(f"Base de datos existente: {self.database_path}")
                
        except Exception as e:
            raise RuntimeError(f"Error al inicializar base de datos: {e}")
    
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
            print(f"Datos cargados desde CSV: {len(df)} registros en tabla 'Registros'")
        except Exception as e:
            print(f"Error al cargar CSV: {e}")
            # Crear tabla vacia
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS Registros (
                    Matricula TEXT PRIMARY KEY,
                    Estado TEXT,
                    "Marca/Modelo" TEXT,
                    Color TEXT,
                    Estatus TEXT,
                    Propietario TEXT,
                    FechaRegistro TEXT,
                    Filename TEXT                    
                )
            """)
            print("Tabla 'Registros' creada (vacia)")
    
    def _signal_handler(self, signum, frame):
        """Maneja la señal de interrupcion (Ctrl+C) para cerrar gracefulmente."""
        print("\n\nDeteniendo procesamiento...")
        self.running = False
    
    # ------------------------------------------------------------------------
    # Metodos de preprocesamiento
    # ------------------------------------------------------------------------
    
    def _prepare_detector_input(self, img: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """
        Prepara la imagen para el detector YOLO.
        
        Parametros
        ----------
        img : np.ndarray
            Imagen de entrada.
        
        Retorna
        -------
        tuple
            (input_data, img_width, img_height)
        """
        img_height, img_width = img.shape[:2]
        
        # Redimensionar a 640x640
        img_resized = cv2.resize(img, (DETECTOR_IMG_SIZE, DETECTOR_IMG_SIZE))
        img_resized = img_resized.astype(np.float32) / 255.0
        img_resized = np.transpose(img_resized, (2, 0, 1))
        input_data = np.expand_dims(img_resized, axis=0)
        
        return input_data, img_width, img_height
    
    def _postprocess_detections(
        self,
        outputs: List[np.ndarray],
        img_width: int,
        img_height: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Postprocesa las salidas del detector YOLO.
        
        Parametros
        ----------
        outputs : list
            Salidas del modelo ONNX.
        img_width : int
            Ancho original de la imagen.
        img_height : int
            Alto original de la imagen.
        
        Retorna
        -------
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
        Preprocesa la imagen para el modelo OCR.
        
        IMPORTANTE: Este preprocesamiento debe ser EXACTAMENTE igual al usado
        durante el entrenamiento del modelo OCR.
        
        Parametros
        ----------
        img : np.ndarray
            Imagen de la placa (ROI).
        
        Retorna
        -------
        np.ndarray
            Imagen preprocesada con dimensiones (1, height, width, channels).
        """
        config = self.ocr_config
        
        # Convertir a escala de grises si es necesario
        if config['image_color_mode'] == 'grayscale':
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        target_h = config['img_height']
        target_w = config['img_width']
        
        # Redimensionar manteniendo aspect ratio
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
        
        # Convertir a float32 sin normalizar (el modelo tiene capa Rescaling)
        img_processed = img_processed.astype(np.float32)
        
        # Asegurar formato de canales
        if config['image_color_mode'] == 'grayscale' and len(img_processed.shape) == 2:
            img_processed = np.expand_dims(img_processed, axis=-1)
        
        # Agregar dimension de batch
        img_processed = np.expand_dims(img_processed, axis=0)
        
        return img_processed
    
    def _decode_ocr_prediction(self, predictions: np.ndarray) -> Tuple[str, List[float]]:
        """
        Decodifica la salida del modelo OCR a texto.
        
        Parametros
        ----------
        predictions : np.ndarray
            Predicciones del modelo con forma (batch, sequence, vocab_size).
        
        Retorna
        -------
        tuple
            (plate_text, confidences)
        """
        # Aplicar softmax
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
    
    # ------------------------------------------------------------------------
    # Metodos de consulta a base de datos
    # ------------------------------------------------------------------------
    
    def _query_database(self, plate: str) -> Optional[Dict]:
        """
        Consulta la base de datos para obtener informacion de la placa.
        
        Parametros
        ----------
        plate : str
            Matricula a consultar.
        
        Retorna
        -------
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
    
    def _save_detection_log(self, plate_text: str, confidence: float, timestamp: str, source: str = "video") -> None:
        """
        Guarda un registro de deteccion en archivo de log.
        
        Parametros
        ----------
        plate_text : str
            Placa reconocida.
        confidence : float
            Confianza del OCR.
        timestamp : str
            Timestamp de la deteccion.
        source : str
            Fuente de la deteccion (video, camera, image).
        """
        log_path = os.path.join(self.output_dir, "detections.log")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{source},{plate_text},{confidence:.4f}\n")
    
    # ------------------------------------------------------------------------
    # Metodos de procesamiento
    # ------------------------------------------------------------------------
    
    def process_image(self, image_path: str) -> Dict:
        """
        Procesa una imagen a traves del pipeline completo.
        
        Parametros
        ----------
        image_path : str
            Ruta a la imagen de entrada.
        
        Retorna
        -------
        dict
            Diccionario con los resultados del pipeline.
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
            print(f"PROCESANDO IMAGEN: {image_path}")
            
            # Cargar imagen
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(f"No se pudo cargar la imagen: {image_path}")
            
            original_img = img.copy()
            
            # Deteccion de placas
            input_data, img_width, img_height = self._prepare_detector_input(original_img)
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, img_width, img_height
            )
            
            # Buscar deteccion de placa (clase 0)
            plate_box = None
            plate_confidence = None
            
            for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if class_id == DETECTOR_PLATE_CLASS_ID:
                    plate_box = box
                    plate_confidence = conf
                    break
            
            if plate_box is None:
                print("No se detectaron placas vehiculares en la imagen")
                results['error'] = "No se detectaron placas"
                return results
            
            x1, y1, x2, y2 = plate_box
            print(f"Placa detectada con confianza: {plate_confidence:.4f}")
            print(f"Coordenadas: ({x1}, {y1}) -> ({x2}, {y2})")
            
            results['detection'] = {
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(plate_confidence)
            }
            
            # Extraccion de ROI
            y1_margin = max(0, y1 - ROI_MARGIN)
            y2_margin = min(original_img.shape[0], y2 + ROI_MARGIN)
            x1_margin = max(0, x1 - ROI_MARGIN)
            x2_margin = min(original_img.shape[1], x2 + ROI_MARGIN)
            
            plate_roi = original_img[y1_margin:y2_margin, x1_margin:x2_margin]
            
            # Guardar ROI
            roi_filename = f"roi_{Path(image_path).stem}.jpg"
            roi_path = os.path.join(self.output_dir, roi_filename)
            cv2.imwrite(roi_path, plate_roi)
            print(f"ROI guardada en: {roi_path}")
            
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
            print(f"Imagen con deteccion guardada en: {full_path}")
            
            # OCR sobre la ROI
            ocr_input = self._preprocess_ocr_image(plate_roi)
            predictions = self.ocr_session.run(
                [self.ocr_output_name],
                {self.ocr_input_name: ocr_input}
            )[0]
            
            plate_text, ocr_confidences = self._decode_ocr_prediction(predictions)
            mean_confidence = np.mean(ocr_confidences) if ocr_confidences else 0
            
            print(f"Placa reconocida: {plate_text}")
            print(f"Confianza promedio: {mean_confidence:.4f}")
            print(f"Confianza por caracter: {[f'{c}:{conf:.4f}' for c, conf in zip(plate_text, ocr_confidences)]}")
            
            results['plate_text'] = plate_text
            results['ocr_confidence'] = mean_confidence
            
            # Consulta a base de datos
            database_record = self._query_database(plate_text)
            
            if database_record:
                print("Registro encontrado:")
                for key, value in database_record.items():
                    print(f"   {key}: {value}")
                results['database_record'] = database_record
            else:
                print(f"No se encontro registro para la placa: {plate_text}")
                results['database_record'] = None
            
            results['success'] = True
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            print(f"\nError en el pipeline: {e}")
            import traceback
            traceback.print_exc()
            return results
    
    def process_frame(self, frame: np.ndarray, save_roi: bool = False, source: str = "video") -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Procesa un solo frame de video para deteccion de placas.
        
        Parametros
        ----------
        frame : np.ndarray
            Frame de video a procesar.
        save_roi : bool
            Si es True, guarda la ROI detectada.
        source : str
            Fuente del video ("video" o "camera").
        
        Retorna
        -------
        tuple
            (frame_annotated, detection_info)
            frame_annotated: Frame con anotaciones dibujadas
            detection_info: Diccionario con informacion de la deteccion o None
        """
        self.frame_count += 1
        
        # Skip frames para mejorar rendimiento
        if self.frame_count % VIDEO_SKIP_FRAMES != 0:
            return frame, None
        
        detection_info = None
        
        try:
            # Deteccion de placas
            input_data, img_width, img_height = self._prepare_detector_input(frame)
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, img_width, img_height
            )
            
            # Buscar deteccion de placa (clase 0)
            for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if class_id == DETECTOR_PLATE_CLASS_ID:
                    x1, y1, x2, y2 = box
                    
                    # Dibujar rectangulo de deteccion
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Placa: {conf:.2f}", (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Extraer ROI
                    y1_margin = max(0, y1 - ROI_MARGIN)
                    y2_margin = min(frame.shape[0], y2 + ROI_MARGIN)
                    x1_margin = max(0, x1 - ROI_MARGIN)
                    x2_margin = min(frame.shape[1], x2 + ROI_MARGIN)
                    
                    plate_roi = frame[y1_margin:y2_margin, x1_margin:x2_margin]
                    
                    # Cooldown: no procesar la misma placa repetidamente
                    current_plate_key = f"{x1},{y1},{x2},{y2}"
                    frames_since_last = self.frame_count - self.last_detection_frame
                    
                    if frames_since_last > DETECTION_COOLDOWN_FRAMES or current_plate_key != self.last_detected_plate:
                        # Procesar OCR
                        ocr_input = self._preprocess_ocr_image(plate_roi)
                        predictions = self.ocr_session.run(
                            [self.ocr_output_name],
                            {self.ocr_input_name: ocr_input}
                        )[0]
                        
                        plate_text, ocr_confidences = self._decode_ocr_prediction(predictions)
                        mean_confidence = np.mean(ocr_confidences) if ocr_confidences else 0
                        
                        # Validar que la placa tenga longitud razonable
                        if len(plate_text) >= 5 and mean_confidence > 0.5:
                            # Consultar base de datos
                            database_record = self._query_database(plate_text)
                            
                            # Guardar deteccion en log
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self._save_detection_log(plate_text, mean_confidence, timestamp, source)
                            
                            # Guardar ROI si se solicita
                            if save_roi:
                                roi_filename = f"roi_{timestamp.replace(' ', '_').replace(':', '-')}.jpg"
                                roi_path = os.path.join(self.output_dir, roi_filename)
                                cv2.imwrite(roi_path, plate_roi)
                            
                            # Mostrar informacion en frame
                            info_text = f"Placa: {plate_text} ({mean_confidence:.2f})"
                            cv2.putText(frame, info_text, (x1, y2 + 25),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
                            if database_record:
                                propietario = database_record.get('Propietario', 'Desconocido')
                                cv2.putText(frame, f"Prop: {propietario}", (x1, y2 + 50),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                            
                            detection_info = {
                                'plate_text': plate_text,
                                'confidence': mean_confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'database_record': database_record,
                                'timestamp': timestamp,
                                'frame_number': self.frame_count
                            }
                            
                            print(f"[Frame {self.frame_count}] Placa detectada: {plate_text} (conf: {mean_confidence:.2f})")
                            
                            # Actualizar estado de cooldown
                            self.last_detected_plate = current_plate_key
                            self.last_detection_frame = self.frame_count
            
            return frame, detection_info
            
        except Exception as e:
            print(f"Error procesando frame: {e}")
            return frame, None
    
    def process_video_file(
        self,
        video_path: str,
        output_video: Optional[str] = None,
        save_roi: bool = False,
        display: bool = False,
        start_frame: int = 0,
        end_frame: Optional[int] = None
    ) -> Dict:
        """
        Procesa un archivo de video y guarda el resultado.
        
        Parametros
        ----------
        video_path : str
            Ruta al archivo de video de entrada.
        output_video : str, optional
            Ruta para guardar el video procesado.
        save_roi : bool
            Si es True, guarda las ROIs detectadas.
        display : bool
            Si es True, muestra la ventana de video durante el procesamiento.
        start_frame : int
            Frame inicial para procesar.
        end_frame : int, optional
            Frame final para procesar.
        
        Retorna
        -------
        dict
            Estadisticas del procesamiento.
        """
        print(f"\nProcesando archivo de video: {video_path}")
        
        # Verificar que el archivo existe
        if not Path(video_path).exists():
            raise FileNotFoundError(f"No se encontro el video: {video_path}")
        
        # Inicializar captura de video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir el video: {video_path}")
        
        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video: {width}x{height}, FPS: {fps:.2f}, Total frames: {total_frames}")
        
        # Configurar rango de frames a procesar
        start_frame = max(0, start_frame)
        if end_frame is None or end_frame > total_frames:
            end_frame = total_frames
        
        print(f"Procesando frames: {start_frame} a {end_frame}")
        
        # Saltar a frame inicial si es necesario
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Inicializar video writer si se solicita
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
            print(f"Guardando video procesado en: {output_video}")
        
        # Variables para estadisticas
        self.frame_count = start_frame
        detection_count = 0
        detections_list = []
        processing_times = []
        
        # Bucle de procesamiento
        self.running = True
        frames_processed = 0
        
        print("\nIniciando procesamiento... (presione Ctrl+C para detener)")
        
        while self.running and self.frame_count < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Procesar frame
            start_time = time.time()
            processed_frame, detection = self.process_frame(frame, save_roi, source="video")
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            if detection:
                detection_count += 1
                detections_list.append(detection)
                print(f"  -> Frame {self.frame_count}: {detection['plate_text']} ({detection['confidence']:.2f})")
            
            # Agregar informacion al frame
            cv2.putText(processed_frame, f"Frame: {self.frame_count}/{end_frame}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(processed_frame, f"Detecciones: {detection_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Guardar frame si se esta grabando
            if self.video_writer:
                self.video_writer.write(processed_frame)
            
            # Mostrar frame si se solicita
            if display:
                # Redimensionar para mostrar si es muy grande
                display_frame = processed_frame
                if width > 1280:
                    display_frame = imutils.resize(processed_frame, width=1280)
                
                cv2.imshow('Procesando Video', display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nDeteniendo procesamiento por solicitud del usuario...")
                    break
            
            self.frame_count += 1
            frames_processed += 1
            
            # Mostrar progreso cada 100 frames
            if frames_processed % 100 == 0:
                progress = (self.frame_count - start_frame) / (end_frame - start_frame) * 100
                print(f"Progreso: {progress:.1f}% - Frames procesados: {frames_processed}")
        
        # Limpiar recursos
        cap.release()
        if self.video_writer:
            self.video_writer.release()
        if display:
            cv2.destroyAllWindows()
        
        # Calcular estadisticas
        avg_processing_time = np.mean(processing_times) if processing_times else 0
        processing_fps = 1.0 / avg_processing_time if avg_processing_time > 0 else 0
        
        stats = {
            'total_frames_processed': frames_processed,
            'detection_count': detection_count,
            'detections': detections_list,
            'avg_processing_time_ms': avg_processing_time * 1000,
            'processing_fps': processing_fps,
            'input_fps': fps,
            'output_video': output_video
        }
        
        print("\n" + "="*50)
        print("PROCESAMIENTO COMPLETADO")
        print("="*50)
        print(f"Frames procesados: {frames_processed}")
        print(f"Detecciones: {detection_count}")
        print(f"Tiempo promedio por frame: {avg_processing_time*1000:.2f} ms")
        print(f"FPS de procesamiento: {processing_fps:.2f}")
        print(f"FPS original del video: {fps:.2f}")
        
        if output_video:
            print(f"Video guardado en: {output_video}")
        
        return stats
    
    def start_real_time(
        self,
        camera_id: int = 0,
        output_video: Optional[str] = None,
        save_roi: bool = False,
        display: bool = True
    ) -> None:
        """
        Inicia la captura y procesamiento en tiempo real desde la camara.
        
        Parametros
        ----------
        camera_id : int
            ID de la camara a usar (default: 0).
        output_video : str, optional
            Ruta para guardar el video procesado.
        save_roi : bool
            Si es True, guarda las ROIs detectadas.
        display : bool
            Si es True, muestra la ventana de video.
        """
        print(f"\nIniciando captura de video desde camara {camera_id}...")
        print("Presione 'q' para salir o Ctrl+C para detener\n")
        
        # Inicializar captura de video
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la camara {camera_id}")
        
        # Configurar resolucion
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Resolucion: {width}x{height}, FPS: {fps}")
        
        # Inicializar video writer si se solicita
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
            print(f"Guardando video en: {output_video}")
        
        # Variables para mostrar FPS
        fps_display = 0
        fps_counter = 0
        fps_timer = time.time()
        
        # Bucle principal
        self.running = True
        self.frame_count = 0
        detection_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("Error al leer frame de la camara")
                break
            
            # Procesar frame
            processed_frame, detection = self.process_frame(frame, save_roi, source="camera")
            
            if detection:
                detection_count += 1
                print(f"Total detecciones: {detection_count}")
            
            # Calcular FPS
            fps_counter += 1
            if time.time() - fps_timer >= 1.0:
                fps_display = fps_counter
                fps_counter = 0
                fps_timer = time.time()
            
            # Mostrar FPS en frame
            cv2.putText(processed_frame, f"FPS: {fps_display}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(processed_frame, f"Detecciones: {detection_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            # Guardar frame si se esta grabando
            if self.video_writer:
                self.video_writer.write(processed_frame)
            
            # Mostrar frame
            if display:
                cv2.imshow('Deteccion de Placas - Tiempo Real', processed_frame)
                
                # Salir con 'q'
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nDeteniendo por solicitud del usuario...")
                    break
        
        # Limpiar recursos
        cap.release()
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()
        
        print(f"\nCaptura finalizada. Total detecciones: {detection_count}")
    
    def __del__(self):
        """Cierra la conexion a la base de datos al destruir el objeto."""
        if hasattr(self, 'conn'):
            self.conn.close()
#endregion

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
    # Modo imagen
    python main.py --image inputs/carro.jpg
    python main.py --image inputs/carro.jpg --output resultados
    
    # Modo video (procesa video guardado)
    python main.py --video inputs/video.mp4
    python main.py --video inputs/video.mp4 --output-video resultado.mp4
    python main.py --video inputs/video.mp4 --save-roi --display
    
    # Modo tiempo real (camara)
    python main.py --camera
    python main.py --camera --camera-id 0 --output-video grabacion.mp4
    python main.py --camera --save-roi --camera-id 1
        """
    )
    
    # Argumentos para modo imagen
    parser.add_argument(
        '--image',
        type=str,
        help='Ruta a la imagen de entrada (modo imagen)'
    )
    
    # Argumentos para modo video
    parser.add_argument(
        '--video',
        type=str,
        help='Ruta al archivo de video de entrada (modo video)'
    )
    
    parser.add_argument(
        '--start-frame',
        type=int,
        default=0,
        help='Frame inicial para procesar video (default: 0)'
    )
    
    parser.add_argument(
        '--end-frame',
        type=int,
        help='Frame final para procesar video'
    )
    
    # Argumentos para modo tiempo real
    parser.add_argument(
        '--camera',
        action='store_true',
        help='Activar modo tiempo real desde camara'
    )
    
    parser.add_argument(
        '--camera-id',
        type=int,
        default=0,
        help='ID de la camara a usar (default: 0)'
    )
    
    # Argumentos generales de video
    parser.add_argument(
        '--save-roi',
        action='store_true',
        help='Guardar las ROIs detectadas'
    )
    
    parser.add_argument(
        '--output-video',
        type=str,
        help='Guardar video procesado en archivo'
    )
    
    parser.add_argument(
        '--display',
        action='store_true',
        help='Mostrar ventana de video durante el procesamiento'
    )
    
    # Argumentos generales
    parser.add_argument(
        '--detector-model',
        type=str,
        default=DETECTOR_MODEL_PATH,
        help=f'Ruta al modelo detector ONNX (default: {DETECTOR_MODEL_PATH})'
    )
    
    parser.add_argument(
        '--ocr-model',
        type=str,
        default=OCR_MODEL_PATH,
        help=f'Ruta al modelo OCR ONNX (default: {OCR_MODEL_PATH})'
    )
    
    parser.add_argument(
        '--ocr-config',
        type=str,
        default=OCR_CONFIG_PATH,
        help=f'Ruta al archivo de configuracion YAML (default: {OCR_CONFIG_PATH})'
    )
    
    parser.add_argument(
        '--database',
        type=str,
        default=DATABASE_PATH,
        help=f'Ruta a la base de datos SQLite (default: {DATABASE_PATH})'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Directorio de salida para resultados (default: outputs)'
    )
    
    args = parser.parse_args()
    
    # Verificar modo de operacion
    modes = sum([bool(args.image), bool(args.video), args.camera])
    if modes == 0:
        print("Error: Debe especificar --image, --video o --camera")
        sys.exit(1)
    if modes > 1:
        print("Error: Solo puede especificar un modo de operacion (--image, --video o --camera)")
        sys.exit(1)
    
    try:
        # Crear pipeline
        # Inicio del pipeline
        start_timestamp = int(time.time() * 1000)
        pipeline = MexicanLicencePlateDetector(
            detector_model_path=args.detector_model,
            ocr_model_path=args.ocr_model,
            ocr_config_path=args.ocr_config,
            database_path=args.database,
            output_dir=args.output
        )
        
        # Modo imagen
        if args.image:
            if not Path(args.image).exists():
                print(f"Error: No se encontro la imagen: {args.image}")
                sys.exit(1)
            
            results = pipeline.process_image(args.image)
            
            # Mostrar resumen final
            print("\n" + "="*50)
            print("Resumen de resultados")
            print("="*50)
            
            if results['success']:
                print(f"Pipeline completado exitosamente")
                print(f"Placa detectada: {results['plate_text']}")
                print(f"Confianza OCR: {results['ocr_confidence']:.4f}")
                print(f"ROI guardada en: {results['roi_path']}")
                
                if results['database_record']:
                    print(f"\nDatos asociados:")
                    for key, value in results['database_record'].items():
                        print(f"   {key}: {value}")
                else:
                    print(f"\nDatos asociados: No encontrados")
            else:
                print(f"Pipeline fallo: {results['error']}")
        
        # Modo video
        elif args.video:
            if not Path(args.video).exists():
                print(f"Error: No se encontro el video: {args.video}")
                sys.exit(1)
            
            # Si no se especifica output_video, crear uno por defecto
            output_video = args.output_video
            if not output_video:
                video_name = Path(args.video).stem
                output_video = os.path.join(args.output, f"{video_name}_processed.mp4")
            
            stats = pipeline.process_video_file(
                video_path=args.video,
                output_video=output_video,
                save_roi=args.save_roi,
                display=args.display,
                start_frame=args.start_frame,
                end_frame=args.end_frame
            )
            
            # Mostrar detecciones
            if stats['detection_count'] > 0:
                print(f"\nDetecciones realizadas:")
                for i, det in enumerate(stats['detections'][:10], 1):  # Mostrar primeras 10
                    print(f"  {i}. Frame {det['frame_number']}: {det['plate_text']} (conf: {det['confidence']:.2f})")
                
                if stats['detection_count'] > 10:
                    print(f"  ... y {stats['detection_count'] - 10} detecciones mas")
        
        # Modo tiempo real
        else:
            pipeline.start_real_time(
                camera_id=args.camera_id,
                output_video=args.output_video,
                save_roi=args.save_roi,
                display=not args.display  # Para camara, display es True por defecto
            )
        end_timestamp = int(time.time() * 1000)
        print(f"Tiempo total (ms): {end_timestamp-start_timestamp}")

    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#endregion