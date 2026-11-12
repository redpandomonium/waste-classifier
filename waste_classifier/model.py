"""Transfer-learning model: a pretrained mobile backbone with a small classifier head."""

from __future__ import annotations

import tensorflow as tf

from .data import CLASS_NAMES, IMAGE_SIZE

_apps = tf.keras.applications

# name -> (constructor, needs_scaling). Every model here takes [0, 255] pixels:
# MobileNetV2 wants [-1, 1], so a Rescaling layer is added in front of it; the
# others do their own scaling internally.
BACKBONES = {
    "mobilenetv2": (_apps.MobileNetV2, True),
    "mobilenetv3small": (_apps.MobileNetV3Small, False),
    "mobilenetv3large": (_apps.MobileNetV3Large, False),
    "efficientnetb0": (_apps.EfficientNetB0, False),
    "efficientnetv2b0": (_apps.EfficientNetV2B0, False),
}
DEFAULT_BACKBONE = "mobilenetv2"


def build_feature_extractor(
    backbone: str = DEFAULT_BACKBONE, weights: str | None = "imagenet"
) -> tf.keras.Model:
    """[0, 255] image -> pooled feature vector, with the backbone frozen."""
    constructor, needs_scaling = BACKBONES[backbone]
    inputs = tf.keras.Input((IMAGE_SIZE, IMAGE_SIZE, 3), name="image")
    x = inputs
    if needs_scaling:
        x = tf.keras.layers.Rescaling(1.0 / 127.5, offset=-1.0, name="scale_to_minus1_1")(x)
    base = constructor(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3),
        include_top=False,
        weights=weights,
        pooling="avg",
    )
    base.trainable = False
    # training=False keeps batch-norm statistics frozen, also during fine-tuning.
    outputs = base(x, training=False)
    return tf.keras.Model(inputs, outputs, name=f"{backbone}_features")


def build_model(
    num_classes: int = len(CLASS_NAMES),
    weights: str | None = "imagenet",
    dropout: float = 0.2,
    backbone: str = DEFAULT_BACKBONE,
) -> tf.keras.Model:
    """Input: 224x224x3 image with values in [0, 255]. Output: class probabilities."""
    features = build_feature_extractor(backbone, weights)
    x = tf.keras.layers.Dropout(dropout)(features.output)
    outputs = tf.keras.layers.Dense(
        num_classes, activation="softmax", name="probabilities")(x)
    return tf.keras.Model(features.input, outputs, name="waste_classifier")


def get_backbone(model: tf.keras.Model) -> tf.keras.Model:
    for layer in model.layers:
        if isinstance(layer, tf.keras.Model):
            return layer
    raise ValueError("Backbone not found in model")


def unfreeze_top(model: tf.keras.Model, trainable_layers: int = 50) -> None:
    """Make the last `trainable_layers` backbone layers trainable for fine-tuning."""
    backbone = get_backbone(model)
    backbone.trainable = True
    for layer in backbone.layers[:-trainable_layers]:
        layer.trainable = False


def compile_model(model: tf.keras.Model, learning_rate: float) -> None:
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
