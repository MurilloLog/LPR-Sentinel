"""
Modulo de inferencia para reconocimiento de placas vehiculares.

Este modulo proporciona funcionalidades para cargar un modelo entrenado de reconocimiento
de placas y realizar inferencias sobre imagenes, incluyendo diagnostico de diferentes
estrategias de normalizacion.
"""

import os
import argparse
import cv2
import numpy as np
import yaml
from tensorflow import keras

from fast_plate_ocr.train.model.layers import (
    MaxBlurPooling2D,
    PatchExtractor,
    MLP,
    PositionEmbedding,
    TransformerBlock,
    TokenReducer,
    VocabularyProjection
)


# -----------------------------------------------------------------------------
# Constantes de configuracion
# -----------------------------------------------------------------------------

MODEL_PATH = "trained_models/2026-03-13_13-53-22/ckpt-epoch_71-acc_0.979.keras"
PLATE_CONFIG_PATH = "./config/plate_config.yaml"

CUSTOM_OBJECTS = {
    "MaxBlurPooling2D": MaxBlurPooling2D,
    "PatchExtractor": PatchExtractor,
    "MLP": MLP,
    "PositionEmbedding": PositionEmbedding,
    "TransformerBlock": TransformerBlock,
    "TokenReducer": TokenReducer,
    "VocabularyProjection": VocabularyProjection,
}


# -----------------------------------------------------------------------------
# Funciones de configuracion
# -----------------------------------------------------------------------------

def load_plate_config(config_path):
    """
    Carga la configuracion de placas desde un archivo YAML.

    Parametros
    ----------
    config_path : str
        Ruta al archivo de configuracion YAML.

    Retorna
    -------
    dict
        Diccionario con los parametros de configuracion.
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


# -----------------------------------------------------------------------------
# Preprocesamiento de imagenes
# -----------------------------------------------------------------------------

def preprocess_image(img_path, config, normalization='minmax'):
    """
    Preprocesa una imagen para ser utilizada como entrada del modelo.

    Parametros
    ----------
    img_path : str
        Ruta a la imagen a procesar.
    config : dict
        Diccionario de configuracion con parametros de preprocesamiento.
    normalization : str, opcional
        Tipo de normalizacion a aplicar. Opciones: 'minmax' (0-1), 'std' (0-255), 'none'.
        Por defecto 'minmax'.

    Retorna
    -------
    np.ndarray
        Imagen preprocesada con dimensiones (1, height, width, channels).

    Lanza
    -----
    FileNotFoundError
        Si no se encuentra la imagen en la ruta especificada.
    """
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"No se encontro la imagen: {img_path}")

    if config['image_color_mode'] == 'grayscale':
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    target_h = config['img_height']
    target_w = config['img_width']

    if config['keep_aspect_ratio']:
        h, w = img.shape[:2]
        aspect = w / h

        if w / h > target_w / target_h:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)

        interpolation = cv2.INTER_LINEAR if config['interpolation'] == 'linear' else cv2.INTER_CUBIC
        img_resized = cv2.resize(img, (new_w, new_h), interpolation=interpolation)

        if config['image_color_mode'] == 'grayscale':
            canvas = np.zeros((target_h, target_w), dtype=np.float32)
        else:
            canvas = np.zeros((target_h, target_w, 3), dtype=np.float32)

        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2

        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = img_resized
        img_processed = canvas
    else:
        img_processed = cv2.resize(img, (target_w, target_h))

    if normalization == 'minmax':
        img_processed = img_processed.astype(np.float32) / 255.0
    elif normalization == 'std':
        img_processed = img_processed.astype(np.float32)
        img_processed = (img_processed - 127.5) / 127.5
    else:
        img_processed = img_processed.astype(np.float32)

    if config['image_color_mode'] == 'grayscale' and len(img_processed.shape) == 2:
        img_processed = np.expand_dims(img_processed, axis=-1)

    img_processed = np.expand_dims(img_processed, axis=0)

    return img_processed


# -----------------------------------------------------------------------------
# Funciones de inferencia
# -----------------------------------------------------------------------------

def apply_softmax(logits):
    """
    Aplica la funcion softmax a los logits para obtener probabilidades.

    Parametros
    ----------
    logits : np.ndarray
        Matriz de logits de entrada.

    Retorna
    -------
    np.ndarray
        Matriz de probabilidades resultante.
    """
    exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
    return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)


def decode_prediction(predictions, alphabet):
    """
    Decodifica la salida del modelo a texto legible.

    Parametros
    ----------
    predictions : np.ndarray
        Predicciones del modelo con forma (batch, sequence, vocab_size).
    alphabet : str
        Cadena que contiene el vocabulario utilizado por el modelo.

    Retorna
    -------
    tuple
        Tupla que contiene (texto_decodificado, lista_confianzas, indices_predichos, probabilidades).
    """
    probs = apply_softmax(predictions[0])
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


# -----------------------------------------------------------------------------
# Funciones de diagnostico
# -----------------------------------------------------------------------------

def test_normalizations(test_image, config, model, alphabet):
    """
    Prueba diferentes tipos de normalizacion para determinar la mas adecuada.

    Parametros
    ----------
    test_image : str
        Ruta a la imagen de prueba.
    config : dict
        Diccionario de configuracion.
    model : keras.Model
        Modelo cargado para inferencia.
    alphabet : str
        Vocabulario del modelo.

    Retorna
    -------
    tuple
        Tupla que contiene (mejor_normalizacion, mejor_resultado).
    """
    normalizations = ['minmax', 'std', 'none']
    best_confidence = 0
    best_result = None
    best_norm = None

    #print("\n" + "=" * 70)
    #print("PROBANDO DIFERENTES NORMALIZACIONES")
    #print("=" * 70)

    for norm in normalizations:
        #print(f"\nProbando normalizacion: {norm}")
        #print("-" * 50)

        try:
            img_processed = preprocess_image(test_image, config, normalization=norm)
            predictions = model.predict(img_processed, verbose=0)

            plate_text, confidences, pred_indices, probs = decode_prediction(predictions, alphabet)
            avg_confidence = np.mean(confidences)

            #print(f"  Placa: {plate_text}")
            #print(f"  Confianza promedio: {avg_confidence:.4f}")
            #print(f"  Rango de probabilidades: [{np.min(probs):.4f}, {np.max(probs):.4f}]")
            #print(f"  Distribucion: max prob={np.max(probs):.4f}, min prob={np.min(probs):.4f}")

            if avg_confidence > best_confidence:
                best_confidence = avg_confidence
                best_result = (plate_text, confidences, pred_indices, probs)
                best_norm = norm

        except Exception as e:
            print(f"  Error: {e}")

    return best_norm, best_result


def inspect_model_input(model):
    """
    Inspecciona la estructura del modelo para identificar capas de normalizacion.

    Parametros
    ----------
    model : keras.Model
        Modelo a inspeccionar.

    Retorna
    -------
    tuple
        Tupla que contiene (tiene_batch_norm, tiene_rescaling).
    """
    #print("\n" + "=" * 70)
    #print("INSPECCIONANDO MODELO")
    #print("=" * 70)

    first_layer = model.layers[0]
    #print(f"Primera capa: {first_layer.name}")
    #print(f"Tipo: {type(first_layer).__name__}")

    if hasattr(first_layer, 'batch_input_shape'):
        print(f"Input shape esperado: {first_layer.batch_input_shape}")

    has_batch_norm = False
    has_rescaling = False

    for layer in model.layers:
        if 'BatchNormalization' in str(type(layer)):
            has_batch_norm = True
            #print(f"  Capa BatchNormalization encontrada: {layer.name}")
        if 'Rescaling' in str(type(layer)):
            has_rescaling = True
            #print(f"  Capa Rescaling encontrada: {layer.name}")

    if has_batch_norm:
        print("\nEl modelo tiene BatchNormalization, lo que sugiere que espera valores normalizados.")
    if has_rescaling:
        print("\nEl modelo tiene Rescaling, que puede estar normalizando internamente.")

    return has_batch_norm, has_rescaling


# -----------------------------------------------------------------------------
# Punto de entrada principal
# -----------------------------------------------------------------------------
# Run as: python .\inference.py --input_dir ./140x70_dataset/val/"xxxxx.jpg"
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FastPlateOCR inferencer')
    parser.add_argument('--input_dir', type=str, required=True, help='Imagen de entrada')  # argumento posicional
    args = parser.parse_args()
    test_image = args.input_dir
    #test_image = "test2.jpg"

    try:
        #print("\n[1/5] Cargando configuracion...")
        config = load_plate_config(PLATE_CONFIG_PATH)
        alphabet = config['alphabet']

        #print(f"  - Alphabet ({len(alphabet)} chars)")
        #print(f"  - Max slots: {config['max_plate_slots']}")
        #print(f"  - Image size: {config['img_height']}x{config['img_width']}")

        #print("\n[2/5] Cargando modelo...")
        model = keras.models.load_model(
            MODEL_PATH,
            compile=False,
            custom_objects=CUSTOM_OBJECTS
        )
        #print(f"  - Output shape: {model.output_shape}")

        #print("\n[3/5] Inspeccionando modelo...")
        has_batch_norm, has_rescaling = inspect_model_input(model)

        #print("\n[4/5] Probando diferentes normalizaciones...")
        best_norm, best_result = test_normalizations(
            test_image,
            config,
            model,
            alphabet
        )

        #print("\n[5/5] Mostrando mejor resultado...")
        if best_result:
            plate_text, confidences, pred_indices, probs = best_result

            #print("\n" + "=" * 70)
            #print("MEJOR RESULTADO")
            #print("=" * 70)
            #print(f"Normalizacion utilizada: {best_norm}")
            print(f"Placa detectada: {plate_text}")
            print(f"Confianza promedio: {np.mean(confidences):.4f}")

            if np.mean(confidences) > 0.75:
                print("\nLa confianza es aceptable. La prediccion es confiable.")
            else:
                print("\nLa confianza sigue siendo baja. Posibles causas:")
                print("   1. La imagen de prueba no es representativa del dataset de entrenamiento")
                print("   2. El modelo necesita ser re-entrenado con mas datos")
                print("   3. La imagen tiene mala calidad o esta mal enfocada")
                print("   4. El modelo puede estar esperando un preprocesamiento adicional")

            '''expected = "AAD-382-F"
            print(f"\nPlaca esperada: {expected}")

            if plate_text == expected:
                print("Coincidencia perfecta")
            else:
                print("No coincide con la esperada")

                print("\nVerificando si la placa esperada esta entre las predicciones:")
                for slot, expected_char in enumerate(expected):
                    if slot < len(probs):
                        expected_idx = alphabet.find(expected_char)
                        if expected_idx >= 0:
                            prob_expected = probs[slot][expected_idx]
                            print(f"  Slot {slot+1}: '{expected_char}' tiene probabilidad {prob_expected:.4f}")

                            top3_indices = np.argsort(probs[slot])[-3:][::-1]
                            top3_chars = [alphabet[i] for i in top3_indices]
                            if expected_char in top3_chars:
                                print(f"    Esta en top-3: {top3_chars}")
                            else:
                                print(f"    No esta en top-3: {top3_chars}")

        print("\n" + "=" * 70)'''

    except FileNotFoundError as e:
        print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError al predecir: {e}")
        import traceback
        traceback.print_exc()