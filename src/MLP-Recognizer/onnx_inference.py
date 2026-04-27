import os
import argparse
import cv2
import numpy as np
import yaml
import onnxruntime as ort
import time

# Constantes del modelo
MODEL_ONNX_PATH = "./models/best.onnx"
PLATE_CONFIG_PATH = "./config/plate_config.yaml"

# Funciones de configuracion
def load_plate_config(config_path):
    """
    Carga la configuracion de placas desde un archivo YAML conforme el modelo fue entrenado.
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    return {
        'max_plate_slots': config.get('max_plate_slots', 9),
        'alphabet': config.get('alphabet', '0123456789ABCDEFGHJKLMNPRSTUVWXYZ-'),
        'pad_char': config.get('pad_char', '-'),
        'img_height': config.get('img_height', 70),
        'img_width': config.get('img_width', 140),
        'keep_aspect_ratio': config.get('keep_aspect_ratio', True),
        'interpolation': config.get('interpolation', 'linear'),
        'image_color_mode': config.get('image_color_mode', 'grayscale')
    }

# Preprocesamiento de la imagen de entrada
def preprocess_image_onnx(img_path, config):
    """
    Preprocesa una imagen para garantizar el tamaño esperado.
    
    Parametros
    ----------
    img_path : str
        Ruta a la imagen a procesar.
    config : dict
        Diccionario de configuracion.
    
    Retorna
    -------
    np.ndarray
        Imagen preprocesada con dimensiones (1, height, width, channels)
        y valores en el rango [0-255] (sin normalizar).
    """
    # Cargar imagen
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"No se encontro la imagen: {img_path}")
    
    # Convertir a escala de grises de no estarlo
    if config['image_color_mode'] == 'grayscale':
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    target_h = config['img_height']
    target_w = config['img_width']
    
    # Redimensionar la imagen sin deformar
    if config['keep_aspect_ratio']:
        h, w = img.shape[:2]
        aspect = w / h
        
        if w / h > target_w / target_h:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)
        
        # Interpolacion lineal
        if config['interpolation'] == 'linear':
            interpolation = cv2.INTER_LINEAR
        else:
            interpolation = cv2.INTER_CUBIC
        
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
        # Redimensionar directamente sin mantener aspect ratio
        img_processed = cv2.resize(img, (target_w, target_h))
    
    # NO normalizar aqui porque el modelo tiene capa Rescaling
    # Solo convertir a float32 y mantener valores en [0-255]
    img_processed = img_processed.astype(np.float32)
    
    # Asegurar el formato correcto de canales
    if config['image_color_mode'] == 'grayscale' and len(img_processed.shape) == 2:
        img_processed = np.expand_dims(img_processed, axis=-1)
    
    # Agregar dimension de batch
    img_processed = np.expand_dims(img_processed, axis=0)
    
    return img_processed

# Funciones de inferencia
def softmax(x):
    """Aplica softmax a un array."""
    exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

def decode_prediction(predictions, alphabet):
    """
    Decodifica la salida del modelo a texto legible.
    
    Parametros
    ----------
    predictions : np.ndarray
        Predicciones del modelo con forma (batch, sequence, vocab_size).
    alphabet : str
        Cadena que contiene el vocabulario.
    
    Retorna
    -------
    tuple
        Tupla con (texto_decodificado, confidencias, indices, probabilidades)
    """
    # Aplicar softmax a las predicciones
    probs = softmax(predictions[0])
    
    # Obtener indices con mayor probabilidad
    pred_indices = np.argmax(probs, axis=-1)
    
    chars = []
    confidences = []
    
    for idx, char_idx in enumerate(pred_indices):
        if char_idx < len(alphabet):
            char = alphabet[char_idx]
            prob = probs[idx][char_idx]
            chars.append(char)
            confidences.append(prob)
    
    plate_text = "".join(chars)
    return plate_text, confidences, pred_indices, probs

#region main
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FastPlateOCR ONNX inferencer')
    parser.add_argument('--input_dir', type=str, required=True, help='Imagen de entrada')
    args = parser.parse_args()
    
    test_image = args.input_dir
    
    try:
        # Cargar configuracion del modelo
        config = load_plate_config(PLATE_CONFIG_PATH)
        alphabet = config['alphabet']
        #print(f"  - Alphabet: {alphabet}")
        #print(f"  - Image size: {config['img_height']}x{config['img_width']}")
        
        # Cargar modelo ONNX
        session = ort.InferenceSession(MODEL_ONNX_PATH)
        
        # Obtener informacion del modelo
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        #print(f"  - Input name: {input_name}")
        #print(f"  - Output name: {output_name}")
        #print(f"  - Input shape: {session.get_inputs()[0].shape}")
        
        # Preprocesar imagen
        start = time.time()
        img_processed = preprocess_image_onnx(test_image, config)
        #print(f"  - Input shape: {img_processed.shape}")
        #print(f"  - Value range: [{img_processed.min():.1f}, {img_processed.max():.1f}]")
        
        # Realizar inferencia
        predictions = session.run([output_name], {input_name: img_processed})[0]
        #print(f"  - Output shape: {predictions.shape}")
        
        # Decodificar prediccion
        plate_text, confidences, pred_indices, probs = decode_prediction(predictions, alphabet)
        end = time.time()

        # Mostrar resultados
        print(f"Placa detectada: {plate_text}")
        print(f"Confianza promedio: {np.mean(confidences):.4f}")
        print(f"Tiempo de inferencia: {end-start:.4f} ms")
        
        # Mostrar confianza por slot
        print("\nConfianza por slot:")
        for i, (char, conf) in enumerate(zip(plate_text, confidences)):
            print(f"  Slot {i+1}: '{char}' - {conf:.4f}")
        
        # Mostrar top-3 predicciones para cada slot
        print("\nTop-3 predicciones por slot:")
        for slot_idx in range(min(3, len(probs))):  # Mostrar primeros 3 slots
            slot_probs = probs[slot_idx]
            top3_idx = np.argsort(slot_probs)[-3:][::-1]
            top3_chars = [alphabet[i] for i in top3_idx]
            top3_probs = [slot_probs[i] for i in top3_idx]
            print(f"  Slot {slot_idx+1}:")
            for char, prob in zip(top3_chars, top3_probs):
                print(f"    {char}: {prob:.4f}")
        
        # Validar que el resultado sea razonable
        if np.mean(confidences) > 0.75:
            print("\nLa confianza es aceptable. La prediccion es confiable.")
        else:
            print("\nLa confianza es baja. Posibles causas:")
            print("   1. La imagen tiene calidad diferente al entrenamiento")
            print("   2. El preprocesamiento no coincide exactamente")
            print("   3. La imagen tiene mala iluminacion o esta mal enfocada")
        
    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError al predecir: {e}")
        import traceback
        traceback.print_exc()
#endregion