#python main_tester.py --evaluate --images-dir ./input --ground-truth ground_truth.csv --output-csv resultados.csv

"""
Deteccion y reconocimiento de placas vehiculares

Este script implementa un pipeline de vision por computadora que:
1. Detecta placas vehiculares en una imagen usando un modelo YOLO (ONNX)
2. Extrae la region de interes (ROI) de la placa detectada
3. Realiza OCR sobre la ROI usando un modelo de reconocimiento de texto (ONNX)
4. Consulta una base de datos SQLite para obtener informacion asociada a la placa

Uso:
    Modo individual: python main.py --image ruta/a/imagen.jpg
    Modo evaluacion: python main.py --evaluate --images-dir ./input --ground-truth ground_truth.csv
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
from typing import Tuple, Dict, List, Optional
import time
import psutil
from datetime import datetime

#region Variables
# Rutas de modelos y configuraciones
DETECTOR_MODEL_PATH = "./models/MLP_Detector_v8n.onnx" # Modelo YOLO para deteccion
OCR_MODEL_PATH = "./models/MLP_Recognizer_v2.onnx" # Modelo OCR para reconocimiento
OCR_CONFIG_PATH = "./config/plate_config.yaml" # Configuracion del modelo OCR
DATABASE_PATH = "./database/MLPR.db" # Ruta a la base de datos SQLite
CSV_METADATA_PATH = "./database/license_plates_metadata.csv" # CSV dataset

# Constantes del detector
DETECTOR_IMG_SIZE = 640 # Tamanio de entrada del detector
DETECTOR_CONF_THRESHOLD = 0.5 # Umbral de confianza para deteccion
DETECTOR_NMS_THRESHOLD = 0.45 # Umbral NMS
DETECTOR_PLATE_CLASS_ID = 0 # ID de clase para placa vehicular
ROI_MARGIN = 1 # Margen para extraer ROI
#endregion

#region Main class
class MexicanLicencePlateDetector:
    """
    Procesamiento de placas vehiculares mexicanas
    
    Esta clase integra deteccion, OCR y consulta a base de datos.
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
        
        # Crear directorio de salida si no existe
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Inicializar componentes
        self._load_detector_model()
        self._load_ocr_config()
        self._load_ocr_model()
        self._initialize_database()
        
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
    
    def _normalize_mexican_plate(self, plate_text: str) -> str:
        """
        Normaliza una placa mexicana eliminando caracteres de padding y asegurando formato correcto.
        
        El modelo OCR está entrenado para predecir 9 caracteres (max_plate_slots=9).
        Para placas mexicanas formato "ABC-123-D", se esperan 7 caracteres alfanuméricos + 2 guiones.
        Los caracteres de padding ('-') al final deben ser eliminados.
        
        Parametros
        ----------
        plate_text : str
            Texto predicho por el OCR (ej: "ABC-123-D", "ABC-123--", "ABC123D--", etc.)
        
        Retorna
        -------
        str
            Placa normalizada sin padding (ej: "ABC-123-D")
        """
        if not plate_text:
            return ""
        
        # Eliminar caracteres de padding del final (guiones que son relleno)
        plate_clean = plate_text.rstrip('-')
        
        # Si la placa no tiene guiones pero tiene el patrón LLLNNNL, agregar guiones
        # Formato mexicano: 3 letras + 3 números + 1 letra = 7 caracteres
        if len(plate_clean) == 7 and '-' not in plate_clean:
            # Detectar si cumple patrón: letra letra letra numero numero numero letra
            import re
            if re.match(r'^[A-Z]{3}[0-9]{3}[A-Z]$', plate_clean):
                plate_clean = f"{plate_clean[:3]}-{plate_clean[3:6]}-{plate_clean[6]}"
        
        # Validar formato final (opcional: loguear si no coincide)
        import re
        patron_mexicano = r'^[A-Z]{3}-[0-9]{3}-[A-Z]$'
        if not re.match(patron_mexicano, plate_clean):
            # Intento adicional: si tiene formato LLL-NNN pero falta última letra
            if re.match(r'^[A-Z]{3}-[0-9]{3}$', plate_clean):
                plate_clean = f"{plate_clean}-?"
            # Si tiene formato LLL-NNN-L- (padding extra)
            elif plate_clean.endswith('-') and len(plate_clean) == 9:
                plate_clean = plate_clean.rstrip('-')
            elif len(plate_clean) > 9:
                plate_clean = plate_clean[:9].rstrip('-')
        
        return plate_clean
    # ------------------------------------------------------------------------
    # Metodos de preprocesamiento
    # ------------------------------------------------------------------------
    
    def _prepare_detector_input(self, img_path: str) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """
        Prepara la imagen para el detector YOLO.
        
        Parametros
        ----------
        img_path : str
            Ruta a la imagen de entrada.
        
        Retorna
        -------
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
        Postprocesa las salidas del detector YOLO.
        
        Parametros
        ----------
        outputs : list
            Salidas del modelo ONNX.
        original_img : np.ndarray
            Imagen original para escalado.
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
                # NO filtrar el carácter '-', mantenerlo como parte de la predicción
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

    # ------------------------------------------------------------------------
    # Metodo principal del pipeline
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
            
            # Deteccion de placas
            input_data, original_img, img_width, img_height = self._prepare_detector_input(image_path)
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, original_img, img_width, img_height
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
            # Agregar margen
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
    
    # ------------------------------------------------------------------------
    # Metodos de evaluacion
    # ------------------------------------------------------------------------
    
    def evaluate_batch(
        self,
        images_dir: str,
        ground_truth_file: str,
        output_csv: str = "evaluation_results.csv"
    ) -> None:
        """
        Evalua el sistema con un conjunto de imagenes.
        
        Parametros
        ----------
        images_dir : str
            Directorio con las imagenes.
        ground_truth_file : str
            Archivo CSV con columnas: filename, matricula_real, tipo (nocturna/diurna)
        output_csv : str
            Ruta donde guardar los resultados
        """
        # Cargar ground truth
        if not os.path.exists(ground_truth_file):
            print(f"Error: No se encuentra el archivo {ground_truth_file}")
            return
            
        gt_df = pd.read_csv(ground_truth_file)
        
        # Preparar archivo de resultados
        results = []
        
        # Medir espacio en disco usado por modelos
        espacio_modelos_mb = self._measure_disk_usage()
        
        print("="*80)
        print("INICIANDO EVALUACION DEL SISTEMA LPR")
        print("="*80)
        print(f"Total imagenes a evaluar: {len(gt_df)}")
        print(f"Espacio en disco (modelos+config): {espacio_modelos_mb:.2f} MB")
        print("="*80)
        
        # Iniciar temporizador global
        inicio_evaluacion = time.time()
        
        for idx, row in gt_df.iterrows():
            image_path = os.path.join(images_dir, row['filename'])
            
            if not os.path.exists(image_path):
                print(f"[ADVERTENCIA] Imagen no encontrada: {image_path}")
                # Registrar como error
                record = {
                    'imagen': row['filename'],
                    'tipo': row['tipo'],
                    'matricula_real': row['matricula_real'],
                    'matricula_detectada': '[ARCHIVO_NO_ENCONTRADO]',  # Sin guiones aquí también
                    'acierto': False,
                    'tiempo_ms': 0,
                    'cpu_porcentaje': 0,
                    'ram_mb': 0,
                    'tp': 0,
                    'fn': 1,
                    'fp': 0,
                    'confianza_ocr': 0,
                    'detection_confidence': 0,
                    'error': 'Archivo no encontrado'
                }
                results.append(record)
                continue
            
            # Medir recursos antes de la inferencia
            proceso_actual = psutil.Process()
            ram_before = proceso_actual.memory_info().rss / 1024 / 1024 # MB
            
            # Para CPU: medir durante un intervalo corto antes
            cpu_percent_start = proceso_actual.cpu_percent(interval=0.1)  
            
            # Medir tiempo de respuesta
            start_time = time.time()
            
            # Ejecutar pipeline
            result = self.process_image(image_path)
            
            end_time = time.time()
            
            # Medir recursos después
            cpu_percent_end = proceso_actual.cpu_percent(interval=0.1)
            ram_after = proceso_actual.memory_info().rss / 1024 / 1024
            
            # Calcular consumo
            tiempo_respuesta_ms = (end_time - start_time) * 1000
            cpu_consumo = max(0, cpu_percent_end - cpu_percent_start)
            ram_consumo = max(ram_before, ram_after)  # Pico de memoria
            
            # Evaluar acierto
            matricula_real = row['matricula_real']
            matricula_detectada_raw = result.get('plate_text', '')

            # MANEJO DE None
            if matricula_detectada_raw is None:
                matricula_detectada_raw = ''

            tipo_imagen = row['tipo']

            # Normalizar la placa detectada (eliminar padding, agregar guiones si es necesario)
            if matricula_detectada_raw:
                matricula_detectada = self._normalize_mexican_plate(matricula_detectada_raw)
                # También normalizar la matrícula real para comparación consistente
                matricula_real_normalized = self._normalize_mexican_plate(matricula_real)
            else:
                matricula_detectada = '[NO_DETECTADA]'
                matricula_real_normalized = matricula_real

            # Comparación usando valores normalizados
            acierto = (matricula_real_normalized == matricula_detectada)

            # Para el registro, guardar tanto la raw como la normalizada
            
            # Calcular TP, FP, FN (por imagen)
            tp = 1 if acierto else 0
            fn = 1 if not acierto else 0
            fp = 0  # Asumiendo que no hay falsos positivos (si detecta algo, es TP o FN)
            
            # Obtener confianzas de forma segura
            ocr_confidence = result.get('ocr_confidence', 0)
            if ocr_confidence is None:
                ocr_confidence = 0
                
            detection_confidence = 0
            if result.get('detection'):
                detection_confidence = result.get('detection', {}).get('confidence', 0)
                if detection_confidence is None:
                    detection_confidence = 0
            
            # Guardar resultados
            record = {
                'imagen': row['filename'],
                'tipo': tipo_imagen,
                'matricula_real': matricula_real,  # Original
                'matricula_real_norm': matricula_real_normalized,  # Normalizada
                'matricula_detectada_raw': matricula_detectada_raw,  # Salida cruda del OCR
                'matricula_detectada': matricula_detectada,  # Normalizada para comparación
                'acierto': acierto,
                'tiempo_ms': round(tiempo_respuesta_ms, 2),
                'cpu_porcentaje': round(cpu_consumo, 2),
                'ram_mb': round(ram_consumo, 2),
                'tp': tp,
                'fn': fn,
                'fp': fp,
                'confianza_ocr': round(ocr_confidence, 4),
                'detection_confidence': round(detection_confidence, 4),
                'error': result.get('error', '') if result.get('error') else ''
            }
            
            results.append(record)
            
            # Mostrar progreso
            status = "Ok" if acierto else "Not ok"
            print(f"[{idx+1}/{len(gt_df)}] {status} {row['filename']}: {matricula_detectada} (real: {matricula_real}) - {tiempo_respuesta_ms:.0f}ms")
        
        tiempo_total_evaluacion = time.time() - inicio_evaluacion
        
        # Guardar resultados
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv, index=False)
        
        # Calcular y mostrar metricas finales
        self._print_metrics(results_df, espacio_modelos_mb, tiempo_total_evaluacion)
        
        print(f"\nResultados guardados en: {output_csv}")
        print("Copie este archivo CSV a Excel para analisis adicional.")
    
    def _measure_disk_usage(self) -> float:
        """Mide el espacio en disco usado por modelos y configuraciones."""
        total_mb = 0
        for path in [self.detector_model_path, self.ocr_model_path, self.ocr_config_path]:
            if os.path.exists(path):
                total_mb += os.path.getsize(path) / (1024 * 1024)
        return total_mb
    
    def _print_metrics(self, results_df: pd.DataFrame, disk_usage_mb: float, tiempo_total_evaluacion: float) -> None:
        """Calcula e imprime las metricas finales."""
        total = len(results_df)
        aciertos = results_df['acierto'].sum()
        tp = results_df['tp'].sum()
        fn = results_df['fn'].sum()
        fp = results_df['fp'].sum()
        
        accuracy = aciertos / total if total > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Metricas por tipo de imagen
        diurnas = results_df[results_df['tipo'] == 'diurna']
        nocturnas = results_df[results_df['tipo'] == 'nocturna']
        
        acc_diurna = diurnas['acierto'].sum() / len(diurnas) if len(diurnas) > 0 else 0
        acc_nocturna = nocturnas['acierto'].sum() / len(nocturnas) if len(nocturnas) > 0 else 0
        
        # Metricas de tiempo - filtrar valores > 0
        tiempos_validos = results_df[results_df['tiempo_ms'] > 0]['tiempo_ms']
        tiempo_promedio = tiempos_validos.mean() if len(tiempos_validos) > 0 else 0
        tiempo_std = tiempos_validos.std() if len(tiempos_validos) > 0 else 0
        tiempo_min = tiempos_validos.min() if len(tiempos_validos) > 0 else 0
        tiempo_max = tiempos_validos.max() if len(tiempos_validos) > 0 else 0
        
        # Recursos - limpiar valores None o NaN
        cpu_promedio = results_df['cpu_porcentaje'].fillna(0).mean()
        ram_promedio = results_df['ram_mb'].fillna(0).mean()
        ram_max = results_df['ram_mb'].fillna(0).max()
        
        # Throughput
        throughput = total / tiempo_total_evaluacion if tiempo_total_evaluacion > 0 else 0
        
        print("\n" + "="*80)
        print("RESUMEN DE METRICAS DE EVALUACION")
        print("="*80)
        print("\n[PRECISION Y DESEMPEÑO]")
        print(f"  Accuracy (Tasa de acierto): {accuracy:.2%} ({aciertos}/{total})")
        print(f"  Recall (Sensibilidad):     {recall:.2%}")
        print(f"  Precision:                 {precision:.2%}")
        print(f"  F1-Score:                  {f1_score:.2%}")
        print(f"  Falsos Positivos (FP):     {fp}")
        print(f"  Falsos Negativos (FN):     {fn}")
        print(f"  Verdaderos Positivos (TP): {tp}")
        
        print("\n[DESGLOSE POR TIPO DE IMAGEN]")
        print(f"  Diurnas:   {acc_diurna:.2%} ({diurnas['acierto'].sum()}/{len(diurnas)})")
        print(f"  Nocturnas: {acc_nocturna:.2%} ({nocturnas['acierto'].sum()}/{len(nocturnas)})")
        
        print("\n[TIEMPO DE RESPUESTA]")
        print(f"  Promedio:  {tiempo_promedio:.2f} ms")
        print(f"  Desv. Std: {tiempo_std:.2f} ms")
        print(f"  Min/Max:   {tiempo_min:.2f} / {tiempo_max:.2f} ms")
        print(f"  Total evaluacion: {tiempo_total_evaluacion:.2f} segundos")
        
        print("\n[CONSUMO DE RECURSOS]")
        print(f"  CPU promedio durante inferencia: {cpu_promedio:.2f}%")
        print(f"  RAM promedio por inferencia:     {ram_promedio:.2f} MB")
        print(f"  RAM pico:                        {ram_max:.2f} MB")
        print(f"  Espacio en disco (modelos):      {disk_usage_mb:.2f} MB")
        
        print("\n[OTRAS METRICAS]")
        # Limpiar valores nulos para confianzas
        conf_ocr = results_df['confianza_ocr'].fillna(0)
        conf_det = results_df['detection_confidence'].fillna(0)
        print(f"  Confianza OCR promedio:  {conf_ocr.mean():.4f}")
        print(f"  Confianza deteccion avg: {conf_det.mean():.4f}")
        print(f"  Throughput:              {throughput:.2f} img/segundo ({throughput*60:.2f} img/minuto)")
        
        # Matriz de confianza vs acierto
        aciertos_df = results_df[results_df['acierto'] == True]
        fallos_df = results_df[results_df['acierto'] == False]
        
        conf_aciertos = aciertos_df['confianza_ocr'].fillna(0).mean() if len(aciertos_df) > 0 else 0
        conf_fallos = fallos_df['confianza_ocr'].fillna(0).mean() if len(fallos_df) > 0 else 0
        print(f"  Confianza media (aciertos): {conf_aciertos:.4f}")
        print(f"  Confianza media (fallos):   {conf_fallos:.4f}")
        
        # Errores comunes
        errores = results_df[results_df['error'].str.len() > 0] if 'error' in results_df.columns else pd.DataFrame()
        if len(errores) > 0:
            print(f"\n[ERRORES REGISTRADOS]")
            print(f"  Total imagenes con error: {len(errores)}")
            for error_tipo in errores['error'].value_counts().items():
                print(f"    - {error_tipo[1]}x: {error_tipo[0][:50]}")
        
        print("="*80)
    
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
    Modo individual:
        python main.py --image inputs/carro.jpg
    
    Modo evaluacion por lotes:
        python main.py --evaluate --images-dir ./input --ground-truth ground_truth.csv --output-csv resultados.csv
        """
    )
    
    # Modo individual
    parser.add_argument(
        '--image',
        type=str,
        help='Ruta a la imagen de entrada (modo individual)'
    )
    
    # Modo evaluacion batch
    parser.add_argument(
        '--evaluate',
        action='store_true',
        help='Ejecutar en modo evaluacion por lotes'
    )
    
    parser.add_argument(
        '--images-dir',
        type=str,
        default='input',
        help='Directorio con imagenes para evaluacion (default: input)'
    )
    
    parser.add_argument(
        '--ground-truth',
        type=str,
        default='ground_truth.csv',
        help='Archivo CSV con matricula real y tipo de imagen (default: ground_truth.csv)'
    )
    
    parser.add_argument(
        '--output-csv',
        type=str,
        default='evaluation_results.csv',
        help='Archivo CSV de salida con resultados (default: evaluation_results.csv)'
    )
    
    # Configuracion de modelos
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
    
    # Verificar que las rutas de modelos existen
    if not os.path.exists(args.detector_model):
        print(f"Advertencia: No se encuentra el detector: {args.detector_model}")
    
    if not os.path.exists(args.ocr_model):
        print(f"Advertencia: No se encuentra el modelo OCR: {args.ocr_model}")
    
    if not os.path.exists(args.ocr_config):
        print(f"Advertencia: No se encuentra la configuracion OCR: {args.ocr_config}")
    
    # Crear pipeline
    try:
        pipeline = MexicanLicencePlateDetector(
            detector_model_path=args.detector_model,
            ocr_model_path=args.ocr_model,
            ocr_config_path=args.ocr_config,
            database_path=args.database,
            output_dir=args.output
        )
        
        if args.evaluate:
            # Modo evaluacion batch
            if not os.path.exists(args.ground_truth):
                print(f"Error: No se encuentra el archivo ground truth: {args.ground_truth}")
                sys.exit(1)
            
            if not os.path.exists(args.images_dir):
                print(f"Error: No se encuentra el directorio de imagenes: {args.images_dir}")
                sys.exit(1)
            
            pipeline.evaluate_batch(
                images_dir=args.images_dir,
                ground_truth_file=args.ground_truth,
                output_csv=args.output_csv
            )
            
        elif args.image:
            # Modo individual
            if not Path(args.image).exists():
                print(f"Error: No se encontro la imagen: {args.image}")
                sys.exit(1)
            
            results = pipeline.process_image(args.image)
            
            print("\n" + "="*50)
            print("RESULTADOS")
            print("="*50)
            if results['success']:
                print(f"Placa detectada: {results['plate_text']}")
                print(f"Confianza OCR: {results['ocr_confidence']:.4f}")
                if results.get('database_record'):
                    print("\nDatos en base de datos:")
                    for key, value in results['database_record'].items():
                        print(f"  {key}: {value}")
            else:
                print(f"Error: {results['error']}")
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#endregion