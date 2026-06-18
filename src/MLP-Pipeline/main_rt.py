"""
Detection and recognition of Mexican license plates

This script implements a computer vision pipeline that:
1. Detects license plates in an image, video, or real-time camera feed
2. Extracts the region of interest (ROI) of the detected plate
3. Performs OCR on the ROI using a text recognition model
4. Queries a SQLite database to obtain information associated with the plate

User guide:
    # Image mode (processes a single image)
    python main.py --image image_path.jpg --output-dir outputs
    
    # Video mode (processes a saved video)
    python main.py --video video_path.mp4 --output-video output_video.mp4
    
    # Real-time mode (camera)
    python main.py --camera
"""
#region Imports
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
from datetime import datetime
import time
import signal
#endregion

#region Variables
# Model paths and configurations
DETECTOR_MODEL_PATH = "./models/MLP_Detector_v8n.onnx"
OCR_MODEL_PATH = "./models/MLP_Recognizer_v2.onnx"
OCR_CONFIG_PATH = "./config/plate_config.yaml"
DATABASE_PATH = "./database/MLPR.db"
CSV_METADATA_PATH = "./database/license_plates_metadata.csv"

# Constants for detection (in pixels and porcentage)
DETECTOR_IMG_SIZE = 640
DETECTOR_CONF_THRESHOLD = 0.5
DETECTOR_NMS_THRESHOLD = 0.45
ROI_MARGIN = 1
DETECTOR_PLATE_CLASS_ID = 0
OUTPUT_DIR = "outputs"

# Constants for video processing
VIDEO_SKIP_FRAMES = 1  # To improve performance, process every N frames
DETECTION_COOLDOWN_FRAMES = 30  # Number of frames to wait before a new detection
DEBUG_MODE = False
SAVE_DEBUG_FRAMES = False
DEBUG_OUTPUT_DIR = "debug_outputs"
#endregion

#region Main class
class MexicanLicencePlateDetector:
    """
    A comprehensive pipeline for Mexican license plate detection and recognition.
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
        Initialize the pipeline, loading models, configurations, and database.
        
        Parameters:
        ----------
        detector_model_path : str
            Path for the ONNX detector model.
        ocr_model_path : str
            Path for the ONNX OCR model.
        ocr_config_path : str
            YAML path for the OCR configuration.
        database_path : str
            Path for the SQLite database.
        csv_metadata_path : str
            Path for the CSV file to initialize the database (optional).
        output_dir : str
            Directory where the output files will be saved.
        """
        self.detector_model_path = detector_model_path
        self.ocr_model_path = ocr_model_path
        self.ocr_config_path = ocr_config_path
        self.database_path = database_path
        self.csv_metadata_path = csv_metadata_path
        self.output_dir = output_dir
        
        # Video attributes
        self.last_detected_plate = None
        self.last_detection_frame = 0
        self.frame_count = 0
        self.video_writer = None
        self.running = True
        
        # Make sure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize main modules
        self._load_detector_model()
        self._load_ocr_config()
        self._load_ocr_model()
        self._initialize_database()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Debugging attributes
        self.debug_mode = DEBUG_MODE
        self.save_debug_frames = SAVE_DEBUG_FRAMES
        self.debug_dir = Path(DEBUG_OUTPUT_DIR)
        if self.debug_mode:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            print(f"Debug mode is enabled. Saving frames to: {self.debug_dir}")
        
    #region Initialization Methods
    def analyze_frame_quality(self, frame: np.ndarray, frame_num: int) -> Dict:
        """Quality analysis of the input frame, returning metrics that can help understand detection performance."""
        h, w = frame.shape[:2]
        
        # Statistics of brightness and contrast
        mean_brightness = np.mean(frame)
        std_brightness = np.std(frame)
        
        # Detect if the frame is too dark or too bright
        is_dark = mean_brightness < 80
        is_bright = mean_brightness > 200
        
        # Detect if the frame has low contrast
        is_low_contrast = std_brightness < 30
        
        return {
            'resolution': f"{w}x{h}",
            'mean_brightness': mean_brightness,
            'std_brightness': std_brightness,
            'is_dark': is_dark,
            'is_bright': is_bright,
            'is_low_contrast': is_low_contrast
        }
    
    def _load_detector_model(self) -> None:
        """Load the ONNX detection model for plate detection."""
        try:
            self.detector_session = ort.InferenceSession(self.detector_model_path)
            self.detector_input_name = self.detector_session.get_inputs()[0].name
            print(f"Detector loaded: {self.detector_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading ONNX detector: {e}")
    
    def _load_ocr_config(self) -> None:
        """Load the OCR model configuration from a YAML file."""
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
            print(f"OCR configuration loaded: {self.ocr_config_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading OCR configuration: {e}")

    def _load_ocr_model(self) -> None:
        """Load the ONNX OCR model for text recognition."""
        try:
            self.ocr_session = ort.InferenceSession(self.ocr_model_path)
            self.ocr_input_name = self.ocr_session.get_inputs()[0].name
            self.ocr_output_name = self.ocr_session.get_outputs()[0].name
            print(f"OCR model loaded: {self.ocr_model_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading OCR model: {e}")

    def _initialize_database(self) -> None:
        """Initialize the SQLite database, creating the table if necessary."""
        try:
            # Check if database file exists
            db_exists = Path(self.database_path).exists()
            
            # Connect to the database
            self.conn = sqlite3.connect(self.database_path)
            
            # If the database does not exist or the table is empty, try to load from CSV
            if not db_exists or self._is_table_empty():
                if Path(self.csv_metadata_path).exists():
                    self._load_csv_to_database()
                else:
                    print(f"File not found: {self.csv_metadata_path}")
                    print("The database will be empty initially.")
            else:
                print(f"Database loaded: {self.database_path}")
                
        except Exception as e:
            raise RuntimeError(f"Error initializing database: {e}")

    def _is_table_empty(self) -> bool:
        """Verifies if the 'Registros' table is empty."""
        try:
            query = "SELECT COUNT(*) FROM Registros"
            cursor = self.conn.execute(query)
            count = cursor.fetchone()[0]
            return count == 0
        except sqlite3.OperationalError:
            return True
    
    def _load_csv_to_database(self) -> None:
        """Load the CSV data into the SQLite database."""
        try:
            df = pd.read_csv(self.csv_metadata_path)
            df.to_sql('Registros', self.conn, if_exists='replace', index=False)
            print(f"Data loaded from CSV: {len(df)} records in table 'Registros'")
        except Exception as e:
            print(f"Error loading CSV: {e}")
            # Create empty table if CSV loading fails
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
            print("Table 'Registros' created (empty) due to CSV loading failure.")
    
    def _signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown on Ctrl+C."""
        print("\n\nShutting down gracefully...")
        self.running = False
    #endregion

    #region Image Processing Methods
    def _prepare_detector_input(self, img: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """
        Prepares the input image for the ONNX model detector.
        
        Parameters
        ----------
        img : np.ndarray
            Input image.
        
        Returns
        -------
        tuple
            (input_data, img_width, img_height)
        """
        img_height, img_width = img.shape[:2]
        
        # Resize to 640x640 px
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
        Postprocess the outputs of the ONNX model detector.
        
        Parameters
        ----------
        outputs : list
            Outputs of the ONNX model.
        img_width : int
            Original width of the image.
        img_height : int
            Original height of the image.
        
        Returns
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
        
        # Filter by confidence threshold
        mask = confidences > DETECTOR_CONF_THRESHOLD
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]
        
        # Transform [x_center, y_center, width, height] to [x1, y1, x2, y2]
        x_center = boxes[:, 0]
        y_center = boxes[:, 1]
        width = boxes[:, 2]
        height = boxes[:, 3]
        
        # Scale to original dimensions
        scale_x = img_width / DETECTOR_IMG_SIZE
        scale_y = img_height / DETECTOR_IMG_SIZE
        
        x1 = (x_center - width / 2) * scale_x
        y1 = (y_center - height / 2) * scale_y
        x2 = (x_center + width / 2) * scale_x
        y2 = (y_center + height / 2) * scale_y
        
        boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1).astype(np.int32)
        
        # Apply Non-Maximum Suppression (NMS)
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
    
    #region OCR Preprocessing Methods
    def _preprocess_ocr_image(self, img: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for the OCR model.
        
        Parameters
        ----------
        img : np.ndarray
            Image of the license plate (ROI).
        
        Returns
        -------
        np.ndarray
            Preprocessed image with shape (1, height, width, channels).
        """
        config = self.ocr_config
        
        # BGR2GRAY convertion
        if config['image_color_mode'] == 'grayscale':
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        
        target_h = config['img_height']
        target_w = config['img_width']
        
        # Resize with aspect ratio preservation and padding
        if config['keep_aspect_ratio']:
            h, w = img.shape[:2]
            aspect = w / h
            
            if w / h > target_w / target_h:
                new_w = target_w
                new_h = int(target_w / aspect)
            else:
                new_h = target_h
                new_w = int(target_h * aspect)
            
            # Interpolation method
            interpolation = cv2.INTER_LINEAR if config['interpolation'] == 'linear' else cv2.INTER_CUBIC
            
            img_resized = cv2.resize(img, (new_w, new_h), interpolation=interpolation)
            
            # Padding mask
            if config['image_color_mode'] == 'grayscale':
                canvas = np.zeros((target_h, target_w), dtype=np.float32)
            else:
                canvas = np.zeros((target_h, target_w, 3), dtype=np.float32)
            
            # Center the resized image on the canvas
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            
            canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = img_resized
            img_processed = canvas
        else:
            img_processed = cv2.resize(img, (target_w, target_h))
        
        # Convert to float32 without normalization
        img_processed = img_processed.astype(np.float32)
        
        # Channel handling for grayscale
        if config['image_color_mode'] == 'grayscale' and len(img_processed.shape) == 2:
            img_processed = np.expand_dims(img_processed, axis=-1)
        
        # Add batch dimension for ONNX model
        img_processed = np.expand_dims(img_processed, axis=0)
        
        return img_processed
    #endregion

    #region OCR Decoding Method
    def _decode_ocr_prediction(self, predictions: np.ndarray) -> Tuple[str, List[float]]:
        """
        Decodes the OCR model output to text.
        
        Parameters
        ----------
        predictions : np.ndarray
            Model predictions with shape (batch, sequence, vocab_size).
        
        Returns
        -------
        tuple
            (plate_text, confidences)
        """
        # Softmax application to get probabilities from logits
        probs = predictions[0]
        exp_probs = np.exp(probs - np.max(probs, axis=-1, keepdims=True))
        softmax_probs = exp_probs / np.sum(exp_probs, axis=-1, keepdims=True)
        
        # Get the index of the character with the highest probability for each position
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
    #endregion

    #region Image Mode Method
    def process_image(self, image_path: str) -> Dict:
        """
        Processes an image through the complete pipeline.
        
        Parameters
        ----------
        image_path : str
            Path to the input image.
        
        Returns
        -------
        dict
            Dictionary with the results of the pipeline.
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
            print(f"\nProcessing image: {image_path}")
            
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(f"Image not found in: {image_path}")
            
            original_img = img.copy()
            
            # Plate detection
            input_data, img_width, img_height = self._prepare_detector_input(original_img)
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, img_width, img_height
            )
            
            # Search for plate detection (class 0)
            plate_box = None
            plate_confidence = None
            
            for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if class_id == DETECTOR_PLATE_CLASS_ID:
                    plate_box = box
                    plate_confidence = conf
                    break
            
            if plate_box is None:
                print("No plate detections found in the image")
                results['error'] = "No plate detections"
                return results
            
            x1, y1, x2, y2 = plate_box
            print(f"Plate detected with confidence: {plate_confidence:.4f}")
            print(f"Coordinates: ({x1}, {y1}), ({x2}, {y2})")
            
            results['detection'] = {
                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                'confidence': float(plate_confidence)
            }
            
            # ROI extraction with margin
            y1_margin = max(0, y1 - ROI_MARGIN)
            y2_margin = min(original_img.shape[0], y2 + ROI_MARGIN)
            x1_margin = max(0, x1 - ROI_MARGIN)
            x2_margin = min(original_img.shape[1], x2 + ROI_MARGIN)
            
            plate_roi = original_img[y1_margin:y2_margin, x1_margin:x2_margin]
            
            # ROI saving
            roi_filename = f"roi_{Path(image_path).stem}.jpg"
            roi_path = os.path.join(self.output_dir, roi_filename)
            cv2.imwrite(roi_path, plate_roi)
            print(f"ROI saved in: {roi_path}")
            
            results['roi_path'] = roi_path
            
            # Draw detection on original image
            cv2.rectangle(original_img, (x1, y1), (x2, y2), (0, 255, 0), 5)
            label = f"Plate: {plate_confidence:.2f}"
            cv2.putText(original_img, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Save image with detection
            final_image = imutils.resize(original_img, width=720)
            full_path = os.path.join(self.output_dir, f"full_{Path(image_path).stem}.jpg")
            cv2.imwrite(full_path, final_image)
            print(f"Image with detection saved in: {full_path}")
            
            # OCR and ROI
            ocr_input = self._preprocess_ocr_image(plate_roi)
            predictions = self.ocr_session.run(
                [self.ocr_output_name],
                {self.ocr_input_name: ocr_input}
            )[0]
            
            plate_text, ocr_confidences = self._decode_ocr_prediction(predictions)
            mean_confidence = np.mean(ocr_confidences) if ocr_confidences else 0
            
            print(f"Plate recognized: {plate_text}")
            print(f"Average confidence: {mean_confidence:.4f}")
            print(f"Confidence by character:\n {[f'{c}:{conf:.4f}' for c, conf in zip(plate_text, ocr_confidences)]}")
            
            results['plate_text'] = plate_text
            results['ocr_confidence'] = mean_confidence
            
            # Database query
            database_record = self._query_database(plate_text)
            
            if database_record:
                print("\nDatabase record found:")
                for key, value in database_record.items():
                    print(f"   {key}: {value}")
                results['database_record'] = database_record
            else:
                print(f"No database record found for plate: {plate_text}")
                results['database_record'] = None
            
            results['success'] = True
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            print(f"\nError in the pipeline: {e}")
            import traceback
            traceback.print_exc()
            return results
    #endregion
    
    #region Video Mode Method
    def process_frame(self, frame: np.ndarray, save_roi: bool = False, source: str = "video") -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Processes a single video frame for license plate detection.
        """
        self.frame_count += 1
        
        # Debugging information
        if self.debug_mode and self.frame_count % 30 == 0:
            print(f"\n [DEBUG] Processing frame {self.frame_count}")
            print(f"   Shape of the frame: {frame.shape}")
            print(f"   Skip frames config: {VIDEO_SKIP_FRAMES}")
        
        # Skip frames to improve performance
        if self.frame_count % VIDEO_SKIP_FRAMES != 0:
            if self.debug_mode and self.frame_count % 30 == 0:
                print(f"   Frame skipped (skip={VIDEO_SKIP_FRAMES})")
            return frame, None
        
        if self.debug_mode and self.frame_count % 30 == 0:
            print(f"   Processing frame (without skip)")
        
        detection_info = None
        
        try:
            # Measure processing time for performance analysis
            start_time = time.time()
            
            # Plate detection
            input_data, img_width, img_height = self._prepare_detector_input(frame)
            
            if self.debug_mode and self.frame_count % 30 == 0:
                print(f"   Input shape: {input_data.shape}")
            
            outputs = self.detector_session.run(None, {self.detector_input_name: input_data})
            
            if self.debug_mode and self.frame_count % 30 == 0:
                print(f"   Outputs with shape: {outputs[0].shape}")
            
            boxes, confidences, class_ids = self._postprocess_detections(
                outputs, img_width, img_height
            )
            
            if self.debug_mode and self.frame_count % 30 == 0:
                print(f"   Detections found: {len(boxes)}")
                if len(boxes) > 0:
                    print(f"   Confidences: {confidences}")
                    print(f"   Class IDs: {class_ids}")
            
            # Search for plate detections (class 0)
            plates_found = 0
            for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if class_id == DETECTOR_PLATE_CLASS_ID:
                    plates_found += 1
                    x1, y1, x2, y2 = box
                    
                    if self.debug_mode:
                        print(f"\n   Plate detected in frame {self.frame_count}:")
                        print(f"      Bounding box: ({x1},{y1}),  ({x2},{y2})")
                        print(f"      Size: {x2-x1}x{y2-y1} px")
                        print(f"      Detection confidence: {conf:.4f}")
                    
                    # Validate minimum size
                    if (x2 - x1) < 30 or (y2 - y1) < 15:
                        if self.debug_mode:
                            print(f"      Detection rejected due to small size")
                        continue
                    
                    # Draw detection on frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"Plate: {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # ROI extraction with margin
                    y1_margin = max(0, y1 - ROI_MARGIN)
                    y2_margin = min(frame.shape[0], y2 + ROI_MARGIN)
                    x1_margin = max(0, x1 - ROI_MARGIN)
                    x2_margin = min(frame.shape[1], x2 + ROI_MARGIN)
                    
                    plate_roi = frame[y1_margin:y2_margin, x1_margin:x2_margin]
                    
                    if self.debug_mode:
                        print(f"      ROI extracted: {plate_roi.shape}")
                    
                    # Cooldown
                    current_plate_key = f"{x1},{y1},{x2},{y2}"
                    frames_since_last = self.frame_count - self.last_detection_frame
                    
                    if frames_since_last > DETECTION_COOLDOWN_FRAMES or current_plate_key != self.last_detected_plate:
                        # Perform OCR on the ROI
                        ocr_input = self._preprocess_ocr_image(plate_roi)
                        predictions = self.ocr_session.run(
                            [self.ocr_output_name],
                            {self.ocr_input_name: ocr_input}
                        )[0]
                        
                        plate_text, ocr_confidences = self._decode_ocr_prediction(predictions)
                        mean_confidence = np.mean(ocr_confidences) if ocr_confidences else 0
                        
                        #if self.debug_mode:
                        #    print(f"      OCR inference: '{plate_text}' (confidence: {mean_confidence:.4f})")
                        
                        # Draw OCR inference on frame
                        info_text = f"OCR: {plate_text} ({mean_confidence:.2f})"
                        cv2.putText(frame, info_text, (x1, y2 + 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                        
                        # Database query
                        database_record = None
                        if len(plate_text) >= 5:
                            database_record = self._query_database(plate_text)
                        
                        # Display database information below the detection
                        y_offset = y2 + 50
                        if database_record:
                            for key, value in database_record.items():
                                if key != 'Matricula' and value and str(value).strip():
                                    text = f"{key}: {value}"
                                    if len(text) > 40:
                                        text = text[:37] + "..."
                                    cv2.putText(frame, text, (x1, y_offset),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (75, 200, 200), 2)
                                    y_offset += 20
                                    if y_offset > frame.shape[0] - 10:
                                        break
                        else:
                            # Display "No record found" message only if the plate seems valid
                            if len(plate_text) >= 5:
                                cv2.putText(frame, "No record found in DB", (x1, y_offset),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (75, 200, 200), 2)
                        
                        # Save to log and DB only if confidence is acceptable
                        if len(plate_text) >= 5 and mean_confidence > 0.3:
                            #database_record = self._query_database(plate_text)
                            
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            self._save_detection_log(plate_text, mean_confidence, timestamp, source)
                            
                            detection_info = {
                                'plate_text': plate_text,
                                'confidence': mean_confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'database_record': database_record,
                                'timestamp': timestamp,
                                'frame_number': self.frame_count
                            }
                            
                            print(f"\n[Frame {self.frame_count}] Plate detected: {plate_text} (confidence: {mean_confidence:.2f})")
                            
                            if database_record:
                                print(f"   Data found in DB:")
                                for key, value in database_record.items():
                                    if value:
                                        print(f"    {key}: {value}")
                            else:
                                print(f"   No record found in DB")

                            # Update cooldown tracking
                            self.last_detected_plate = current_plate_key
                            self.last_detection_frame = self.frame_count
                        #else:
                        #    if len(plate_text) >= 5:
                        #        print(f"OCR inferenced (low confidence): {plate_text}")
                    else:
                        # If it's in cooldown, still show the text of the last detection
                        if self.last_detected_plate:
                            cv2.putText(frame, f"Last: {self.last_detected_plate[:15]}", (x1, y2 + 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
            
            if self.debug_mode and self.frame_count % 30 == 0:
                processing_time = (time.time() - start_time) * 1000
                print(f"Processing time: {processing_time:.1f} ms")
                print(f"Total plates found in frame: {plates_found}")
                
                if plates_found == 0 and self.frame_count % 60 == 0:
                    # Guardar frame para análisis
                    debug_path = self.debug_dir / f"no_detection_frame_{self.frame_count:06d}.jpg"
                    cv2.imwrite(str(debug_path), frame)
                    print(f"    Frame without detections saved: {debug_path}")
            
            return frame, detection_info
            
        except Exception as e:
            print(f" Error processing frame {self.frame_count}: {e}")
            import traceback
            traceback.print_exc()
            return frame, None
    #endregion

    #region Database Query Methods
    def _query_database(self, plate: str) -> Optional[Dict]:
        """
        Database query to retrieve information about a license plate.
        
        Parameters
        ----------
        plate : str
            License plate to query.
        
        Returns
        -------
        dict or None
            Dictionary with the plate data or None if not found.
        """
        try:
            query = "SELECT * FROM Registros WHERE Matricula = ?"
            cursor = self.conn.execute(query, (plate,))
            row = cursor.fetchone()
            
            if row:
                # Get column names from cursor description
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
            
        except sqlite3.Error as e:
            print(f"Error in database query: {e}")
            return None
    
    def _save_detection_log(self, plate_text: str, confidence: float, timestamp: str, source: str = "video") -> None:
        """
        Saves a detection record in the log file.
        
        Parameters
        ----------
        plate_text : str
            License plate recognized.
        confidence : float
            OCR confidence.
        timestamp : str
            Detection timestamp.
        source : str
            Source of the detection (video, camera, image).
        """
        log_path = os.path.join(self.output_dir, "detections.log")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp},{source},{plate_text},{confidence:.4f}\n")
    
    def __del__(self):
        """Closes the database connection when the object is deleted."""
        if hasattr(self, 'conn'):
            self.conn.close()
    #endregion
    
    #region Video Processing Methods
    def test_single_frame(self, video_path: str, frame_number: int = 0):
        """
        Tests a specific frame of the video for debugging purposes.
        """
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"Error: Frame {frame_number} is not available in the video.")
            return
        
        print(f"\nTesting frame {frame_number}")
        
        # Quality analysis
        quality = self.analyze_frame_quality(frame, frame_number)
        print(f"Quality of the frame:")
        print(f"  - Resolution: {quality['resolution']}")
        print(f"  - Mean Brightness: {quality['mean_brightness']:.1f}")
        print(f"  - Contrast: {quality['std_brightness']:.1f}")
        
        # Process the frame
        processed_frame, detection = self.process_frame(frame, save_roi=True, source="test")
        
        # Save the processed frame for review
        test_output = self.debug_dir / f"test_frame_{frame_number}.jpg"
        cv2.imwrite(str(test_output), processed_frame)
        print(f"\n Processed frame saved in: {test_output}")
        
        if detection:
            print(f"  Plate: {detection['plate_text']}")
            print(f"  Confidence: {detection['confidence']:.4f}")
        else:
            print(f"\n No plates detected in this frame")
            
            # Save raw frame for manual analysis
            raw_output = self.debug_dir / f"test_frame_{frame_number}_raw.jpg"
            cv2.imwrite(str(raw_output), frame)
            print(f"  Original frame saved in: {raw_output}")
        
        return detection
    
    def process_frame_with_number(self, frame: np.ndarray, frame_number: int, save_roi: bool = False, source: str = "video") -> Tuple[np.ndarray, Optional[Dict]]:
        """
        Wrapper for process_frame that allows specifying the frame number for logging and debugging.
        """
        # Temporarily set the frame count to the specified frame number for accurate logging
        original_frame_count = self.frame_count
        self.frame_count = frame_number
        
        # Process the frame
        result = self.process_frame(frame, save_roi, source)
        
        # Restore frame_count
        self.frame_count = original_frame_count
        
        return result
    
    #region Video Mode Method
    def process_video_file(self, video_path: str, output_video: Optional[str] = None, save_roi: bool = False, display: bool = False, start_frame: int = 0, end_frame: Optional[int] = None) -> Dict:
        """
        Processes a video file and saves the result.
        """
        print(f"\nProcessing video file: {video_path}")
        
        # Verify that the video file exists
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Initialize video capture
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Error opening video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Video: {width}x{height}, FPS: {fps:.2f}, Total frames: {total_frames}")
        
        # Configure frame range
        start_frame = max(0, start_frame)
        if end_frame is None or end_frame > total_frames:
            end_frame = total_frames
        
        print(f"Processing frames: {start_frame} to {end_frame} (total: {end_frame - start_frame} frames)")
        print(f"Configuration: Skip frames = {VIDEO_SKIP_FRAMES}, Cooldown = {DETECTION_COOLDOWN_FRAMES}")
        
        # Skip to the initial frame
        if start_frame > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Initialize video writer
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
            print(f"Saving processed video in: {output_video}")
        
        # Variables for statistics
        frame_counter = start_frame
        detection_count = 0
        detections_list = []
        processing_times = []
        self.running = True
        frames_processed = 0
        frames_skipped = 0
        
        print("\nStarting processing... (press Ctrl+C to stop)\n")
        
        if display:
            print("  Display disabled on Windows (OpenCV issue)")
            display = False
            
        while self.running: #and self.frame_count < end_frame:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_counter >= end_frame:
                print(f"\n Limit of frames reached ({end_frame})")
                break
            
            # Frames counter for statistics
            frames_processed += 1
            
            # Process frame
            current_frame_num = frame_counter
            start_time = time.time()
            processed_frame, detection = self.process_frame_with_number(frame, current_frame_num, save_roi, source="video")
            processing_time = (time.time() - start_time) * 1000  # ms
            processing_times.append(processing_time)
            
            # Update detection count and list
            if detection:
                detection_count += 1
                detections_list.append(detection)
                print(f"\n Detection #{detection_count}:")
                print(f"   Frame: {self.frame_count}")
                print(f"   Plate: {detection['plate_text']}")
                print(f"   Confidence: {detection['confidence']:.3f}")
            
            # Add information to the frame
            cv2.putText(processed_frame, f"Frame: {current_frame_num}/{end_frame}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            #cv2.putText(processed_frame, f"Detections: {detection_count}", (10, 60),
            #        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(processed_frame, f"FPS: {1000/processing_time:.1f}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Save frame
            if self.video_writer:
                self.video_writer.write(processed_frame)
            
            # Show progress
            if frames_processed % 30 == 0:
                progress = (frame_counter - start_frame) / (end_frame - start_frame) * 100
                
                avg_time = np.mean(processing_times[-30:]) if processing_times else 0
                
                eta = (avg_time * (end_frame - frame_counter)) / 1000 if avg_time > 0 else 0

                print(f"Progress: {progress:.1f}% | Frame: {frame_counter}/{end_frame} | "
                    f"FPS: {1000/avg_time:.1f} | ETA: {eta:.1f}s")
                
            frame_counter += 1
            
        # Release resources
        cap.release()
        if self.video_writer:
            self.video_writer.release()
        
        # Statistics calculation
        avg_processing_time = np.mean(processing_times) if processing_times else 0
        processing_fps = 1000.0 / avg_processing_time if avg_processing_time > 0 else 0
        
        stats = {
            'total_frames_processed': frames_processed,
            'frames_skipped': frames_skipped,
            'detection_count': detection_count,
            'detections': detections_list,
            'avg_processing_time_ms': avg_processing_time,
            'processing_fps': processing_fps,
            'input_fps': fps,
            'output_video': output_video
        }
        
        print(f"\nFrames processed: {frames_processed}")
        print(f"Frames skipped: {frames_skipped}")
        #print(f"Detections: {detection_count}")
        print(f"Average time per frame: {avg_processing_time:.2f} ms")
        print(f"Processing FPS: {processing_fps:.2f}")
        print(f"Original video FPS: {fps:.2f}")
        
        if output_video:
            print(f"Video saved in: {output_video}")
        
        return stats
    #endregion
    
    #region Real-time Camera Methods
    def start_real_time(
        self,
        camera_id: int = 0,
        output_video: Optional[str] = None,
        save_roi: bool = False,
        display: bool = True
    ) -> None:
        """
        Starts the real-time capture and processing from the camera.
        
        Parameters
        ----------
        camera_id : int
            ID of the camera to use (default: 0).
        output_video : str, optional
            Path to save the processed video.
        save_roi : bool
            If True, saves the detected ROIs.
        display : bool
            If True, displays the video window.
        """
        print(f"\nStarting video capture from camera {camera_id}...")
        print("Press 'q' to quit or Ctrl+C to stop\n")
        
        # Initialize video capture
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_id}")
        
        # Resolution configuration (try to set to 1280x720 for better detection, but may depend on the camera capabilities)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Get camera properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Resolution: {width}x{height}, FPS: {fps}")
        
        # Initialize video writer if requested
        if output_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
            print(f"Saving video in: {output_video}")
        
        # Variables for displaying FPS
        fps_display = 0
        fps_counter = 0
        fps_timer = time.time()
        
        # Main loop
        self.running = True
        self.frame_count = 0
        detection_count = 0
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("Error reading frame from camera")
                break
            
            # Frame processing
            processed_frame, detection = self.process_frame(frame, save_roi, source="camera")
            
            if detection:
                detection_count += 1
                print(f"Total detections: {detection_count}")
            
            # Calculate FPS
            fps_counter += 1
            if time.time() - fps_timer >= 1.0:
                fps_display = fps_counter
                fps_counter = 0
                fps_timer = time.time()
            
            # Display FPS on frame
            cv2.putText(processed_frame, f"FPS: {fps_display}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Save frame if recording
            if self.video_writer:
                self.video_writer.write(processed_frame)
            
            # Display frame
            if display:
                cv2.imshow('Plate detection - Real Time', processed_frame)
                
                # Exit with 'q'
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nStopping by user request...")
                    break
        
        # Release resources
        cap.release()
        if self.video_writer:
            self.video_writer.release()
        cv2.destroyAllWindows()
    #endregion
#endregion

#region main()
def main():
    """
    Main function for command-line interface. Parses arguments and runs the appropriate mode (image, video, or real-time).
    """
    parser = argparse.ArgumentParser(
        description='Mexican Licence Plate Detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
User guide:
    Image mode
    python main_rt.py --image inputs/TestInput.jpg
    python main_rt.py --image inputs/TestInput.png --output outputs/TestOutput.png
    
    Video mode
    python main_rt.py --video inputs/VideoInput.mp4 --output-video outputs/VideoOutput.mp4
    
    Real-time mode (camera)
    python main_rt.py --camera
    python main_rt.py --camera --camera-id 0 --output-video outputs/RecordingOutput.mp4
    """
    )
    
    # Image mode arguments
    parser.add_argument(
        '--image',
        type=str,
        help='Input image file path (image mode)'
    )

    
    # Video mode arguments
    parser.add_argument(
        '--video',
        type=str,
        help='Input video file path (video mode)'
    )
    parser.add_argument(
        '--start-frame',
        type=int,
        default=0,
        help='Start frame for video processing (default: 0)'
    )
    parser.add_argument(
        '--end-frame',
        type=int,
        help='End frame for video processing (default: end of video)'
    )
    parser.add_argument(
        '--output-video',
        type=str,
        help='Save processed video to file'
    )
    parser.add_argument(
        '--display',
        action='store_true',
        help='Display video window during processing'
    )
    parser.add_argument(
        '--test-frame',
        type=int,
        help='Test a specific frame number from the video (for diagnosis, only works with --video)'
    )

    # Real-time mode arguments
    parser.add_argument(
        '--camera',
        action='store_true',
        help='Use camera for real-time detection (real-time mode)'
    )
    parser.add_argument(
        '--camera-id',
        type=int,
        default=0,
        help='Camera ID to use (default: 0)'
    )
    
    # Additional options
    parser.add_argument(
        '--save-roi',
        action='store_true',
        help='Save detected plate ROIs as images (for debugging and analysis)'
    )
    parser.add_argument(
        '--detector-model',
        type=str,
        default=DETECTOR_MODEL_PATH,
        help=f'Detector model path (default: {DETECTOR_MODEL_PATH})'
    )
    parser.add_argument(
        '--ocr-model',
        type=str,
        default=OCR_MODEL_PATH,
        help=f'OCR model path (default: {OCR_MODEL_PATH})'
    )
    parser.add_argument(
        '--ocr-config',
        type=str,
        default=OCR_CONFIG_PATH,
        help=f'OCR configuration file path (default: {OCR_CONFIG_PATH})'
    )
    parser.add_argument(
        '--database',
        type=str,
        default=DATABASE_PATH,
        help=f'Database path (default: {DATABASE_PATH})'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Output directory for results (default: outputs)'
    )
    args = parser.parse_args()
    
    # Check that only one mode is selected
    modes = sum([bool(args.image), bool(args.video), args.camera])
    if modes == 0:
        print("Error: You must specify --image, --video or --camera")
        sys.exit(1)
    if modes > 1:
        print("Error: You can only specify one operation mode (--image, --video or --camera)")
        sys.exit(1)
    
    if args.video and args.test_frame is not None:
        pipeline = MexicanLicencePlateDetector()
        pipeline.test_single_frame(args.video, args.test_frame)
        return
    
    try:
        # Pipeline initialization
        start_timestamp = int(time.time() * 1000)
        pipeline = MexicanLicencePlateDetector(
            detector_model_path=args.detector_model,
            ocr_model_path=args.ocr_model,
            ocr_config_path=args.ocr_config,
            database_path=args.database,
            output_dir=args.output
        )
        
        # Image mode
        if args.image:
            if not Path(args.image).exists():
                print(f"Error: Image not found: {args.image}")
                sys.exit(1)
            
            results = pipeline.process_image(args.image)
            
        # Video mode
        elif args.video:
            if not Path(args.video).exists():
                print(f"Error: video not found: {args.video}")
                sys.exit(1)
            
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
        
        # Real-time mode
        else:
            pipeline.start_real_time(
                camera_id=args.camera_id,
                output_video=args.output_video,
                save_roi=args.save_roi,
                display=not args.display
            )
        end_timestamp = int(time.time() * 1000)
        print(f"\nProcessing time (ms): {end_timestamp-start_timestamp}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#endregion