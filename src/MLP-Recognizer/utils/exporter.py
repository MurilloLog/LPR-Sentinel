import tensorflow as tf
import numpy as np
from fast_plate_ocr.train.model.layers import *

# Guardar referencia original
original_gelu = tf.nn.gelu

# Reemplazar con implementación compatible
def gelu_patched(x, approximate=True):
    """Versión de GELU que no usa Erfc"""
    import math
    if approximate:
        # Versión aproximada con tanh (compatible con ONNX)
        sqrt_2_over_pi = math.sqrt(2.0 / math.pi)
        coef = 0.044715
        tanh_arg = sqrt_2_over_pi * (x + coef * tf.pow(x, 3))
        return 0.5 * x * (1.0 + tf.tanh(tanh_arg))
    else:
        # Versión exacta (también compatible)
        return 0.5 * x * (1.0 + tf.math.erf(x / math.sqrt(2.0)))

# Parchear tf.nn.gelu
tf.nn.gelu = gelu_patched

# Cargar custom objects
CUSTOM_OBJECTS = {
    "MaxBlurPooling2D": MaxBlurPooling2D,
    "PatchExtractor": PatchExtractor,
    "MLP": MLP,
    "PositionEmbedding": PositionEmbedding,
    "TransformerBlock": TransformerBlock,
    "TokenReducer": TokenReducer,
    "VocabularyProjection": VocabularyProjection,
}

# Cargar modelo
print("Cargando modelo...")
model = tf.keras.models.load_model(
    'trained_models/2026-03-20_13-57-21/ckpt-epoch_115-acc_0.981.keras',
    custom_objects=CUSTOM_OBJECTS,
    compile=False
)

print("Modelo cargado exitosamente")

# Exportar a ONNX
print("Exportando a ONNX...")
import tf2onnx

@tf.function
def model_fn(x):
    return model(x, training=False)

input_signature = [tf.TensorSpec(shape=(1, 70, 140, 1), dtype=tf.float32, name='input')]

tf2onnx.convert.from_function(
    model_fn,
    input_signature=input_signature,
    opset=18,
    output_path='best.onnx'
)

print("Exportación completada")

# Restaurar función original
tf.nn.gelu = original_gelu

# Verificar
import onnx
import onnxruntime as ort

onnx_model = onnx.load('best.onnx')
onnx.checker.check_model(onnx_model)

# Probar inferencia
session = ort.InferenceSession('best.onnx')
dummy_input = np.random.randn(1, 70, 140, 1).astype(np.float32)
outputs = session.run(None, {'input': dummy_input})
print(f"Verificación exitosa. Output shape: {outputs[0].shape}")