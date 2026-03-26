import tensorflow as tf
import keras
import tf2onnx

from fast_plate_ocr.train.model.layers import (
    MaxBlurPooling2D,
    PatchExtractor,
    MLP,
    PositionEmbedding,
    TransformerBlock,
    TokenReducer,
    VocabularyProjection
)

CUSTOM_OBJECTS = {
    "MaxBlurPooling2D": MaxBlurPooling2D,
    "PatchExtractor": PatchExtractor,
    "MLP": MLP,
    "PositionEmbedding": PositionEmbedding,
    "TransformerBlock": TransformerBlock,
    "TokenReducer": TokenReducer,
    "VocabularyProjection": VocabularyProjection,
}

model = tf.keras.models.load_model('trained_models/2026-03-20_13-57-21/ckpt-epoch_115-acc_0.981.keras',
                                   compile=False,
                                   custom_objects=CUSTOM_OBJECTS)

#model.summary()
print("\nInput shape:", model.input_shape)
print("Output shape:", model.output_shape)
print(f"TensorFlow: {tf.__version__}")
print(f"Keras: {keras.__version__}")
print(f"tf2onnx: {tf2onnx.__version__}")