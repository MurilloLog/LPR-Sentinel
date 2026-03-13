# inference.py
import os
import cv2
import numpy as np
from tensorflow import keras

# Importa solo tus custom layers
from fast_plate_ocr.train.model.layers import (
    MaxBlurPooling2D,
    PatchExtractor,
    MLP,
    PositionEmbedding,
    TransformerBlock,
    TokenReducer,
    VocabularyProjection
)

# -----------------------------
# Configuración de paths y modelo
# -----------------------------
MODEL_PATH = "trained_models/2026-03-10_12-29-11/ckpt-epoch_45-acc_0.974.keras"
IMG_H = 64
IMG_W = 128
CHANNELS = 3

# Diccionario de custom objects
custom_objects = {
    "MaxBlurPooling2D": MaxBlurPooling2D,
    "PatchExtractor": PatchExtractor,
    "MLP": MLP,
    "PositionEmbedding": PositionEmbedding,
    "TransformerBlock": TransformerBlock,
    "TokenReducer": TokenReducer,
    "VocabularyProjection": VocabularyProjection,
}

# -----------------------------
# Funciones de preprocesamiento
# -----------------------------
def preprocess_image(img_path: str) -> np.ndarray:
    """Lee y preprocesa la imagen para el modelo."""
    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"No se encontró la imagen: {img_path}")
    
    img = cv2.resize(img, (IMG_W, IMG_H))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0  # normalización
    img = np.expand_dims(img, axis=0)  # añadir batch dimension
    return img

# -----------------------------
# Cargar modelo
# -----------------------------
print("Cargando modelo Keras...")
model = keras.models.load_model(MODEL_PATH, compile=False, custom_objects=custom_objects)
print("Modelo cargado exitosamente.")

# -----------------------------
# Función de inferencia
# -----------------------------
def predict_plate(img_path: str) -> str:
    """Realiza inferencia de una imagen de placa."""
    img = preprocess_image(img_path)
    pred = model.predict(img)
    
    # Supongamos que el modelo devuelve logits sobre vocabulario
    pred_indices = np.argmax(pred, axis=-1)[0]  # [0] para batch size = 1
    
    # Aquí deberías convertir índices a caracteres según tu tokenizer/vocab
    # Ejemplo: si tienes un vocab:
    vocab = "0123456789ABCDEFGHJKLMNPRSTUVWXYZ-"  # reemplazar según tu proyecto
    plate_text = "".join([vocab[i] for i in pred_indices if i < len(vocab)])
    
    return plate_text

# -----------------------------
# Ejemplo de uso
# -----------------------------
if __name__ == "__main__":
    test_image = "test3.jpg"  # ruta a la imagen de prueba
    try:
        # Inferencia usando tu función
        result = predict_plate(test_image)
        print(f"Predicción de placa: {result}")

        # DEBUG: inspeccionar logits correctamente
        img_array = preprocess_image(test_image)
        pred = model.predict(img_array)
        print("Forma de la salida:", pred.shape)
        print("Logits del primer slot:", pred[0,0])
        print("Índice máximo del primer slot:", np.argmax(pred[0,0]))
    except Exception as e:
        print(f"Error al predecir: {e}")