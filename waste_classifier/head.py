"""Train only the classifier head, on cached backbone features.

    python -m waste_classifier.head --backbone efficientnetv2b0

The backbone stays frozen, so its output for each image never changes and can be
computed once (eda/extract_features.py). Training the head on those cached
features takes seconds on a laptop CPU, which makes it practical to try many
settings. The trained head is then attached to the backbone to give a normal
image-in, probabilities-out model that exports to TF Lite.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import tensorflow as tf

from .data import CLASS_NAMES
from .evaluate import metrics_from_probabilities, print_metrics
from .export_tflite import export
from .features import DEFAULT_FEATURES_DIR, FeatureSet, available_backbones, load_feature_set
from .model import build_feature_extractor


def build_head(feature_dim: int, dropout: float = 0.2, l2: float = 0.003) -> tf.keras.Model:
    layers = tf.keras.layers
    inputs = tf.keras.Input((feature_dim,), name="features")
    x = layers.Normalization(name="standardize")(inputs)
    x = layers.Dropout(dropout)(x)
    outputs = layers.Dense(
        len(CLASS_NAMES), activation="softmax", name="probabilities",
        kernel_regularizer=tf.keras.regularizers.l2(l2))(x)
    return tf.keras.Model(inputs, outputs, name="head")


def train_head(fs: FeatureSet, learning_rate: float = 1e-3, epochs: int = 30,
               batch_size: int = 256, dropout: float = 0.2, l2: float = 0.003,
               class_weighting: bool = True, patience: int = 5, seed: int = 42,
               callbacks: list | None = None):
    """Returns (head model, history dict). Keeps the best validation epoch."""
    tf.keras.utils.set_random_seed(seed)
    head = build_head(fs.x_train.shape[1], dropout, l2)
    head.get_layer("standardize").adapt(fs.x_train)
    head.compile(optimizer=tf.keras.optimizers.Adam(learning_rate),
                 loss="sparse_categorical_crossentropy", metrics=["accuracy"])

    weights = None
    if class_weighting:
        counts = Counter(fs.y_train.tolist())
        weights = {c: len(fs.y_train) / (len(counts) * n) for c, n in counts.items()}

    stop = tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy", patience=patience, restore_best_weights=True)
    history = head.fit(
        fs.x_train, fs.y_train, validation_data=(fs.x_val, fs.y_val),
        epochs=epochs, batch_size=batch_size, class_weight=weights,
        callbacks=[stop] + (callbacks or []), verbose=0)
    return head, {k: [float(v) for v in vals] for k, vals in history.history.items()}


def assemble(backbone: str, head: tf.keras.Model) -> tf.keras.Model:
    """Backbone + trained head = full model taking a [0, 255] image."""
    features = build_feature_extractor(backbone)
    return tf.keras.Model(features.input, head(features.output), name="waste_classifier")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--backbone", default="efficientnetv2b0")
    parser.add_argument("--data-dir", default=None,
                        help="Dataset folder; only needed the first time")
    parser.add_argument("--features-dir", default=DEFAULT_FEATURES_DIR)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--l2", type=float, default=0.003)
    parser.add_argument("--no-class-weighting", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-export", action="store_true",
                        help="Skip building the full model and the TF Lite file")
    args = parser.parse_args()

    ready = available_backbones(args.features_dir)
    if args.backbone not in ready:
        raise SystemExit(
            f"No cached features for {args.backbone} in {args.features_dir} "
            f"(found: {ready or 'none'}). Run eda/extract_features.py first.")

    fs = load_feature_set(args.backbone, args.data_dir, args.features_dir)
    head, history = train_head(
        fs, args.learning_rate, args.epochs, args.batch_size, args.dropout, args.l2,
        not args.no_class_weighting, seed=args.seed)

    metrics = metrics_from_probabilities(fs.y_test, head.predict(fs.x_test, verbose=0))
    metrics["val_accuracy"] = max(history["val_accuracy"])
    metrics["backbone"] = args.backbone
    metrics["settings"] = {k: v for k, v in vars(args).items()
                           if k in ("learning_rate", "epochs", "batch_size", "dropout", "l2", "seed")}
    metrics["splits"] = fs.report
    print(f"Best validation accuracy: {metrics['val_accuracy']:.4f}")
    print_metrics(metrics)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_export:
        model = assemble(args.backbone, head)
        model.save(output_dir / "waste_classifier.keras")
        tflite_path = export(model, output_dir)
        metrics["tflite_size_mb"] = round(tflite_path.stat().st_size / 1e6, 2)
        print(f"TF Lite model: {tflite_path} ({metrics['tflite_size_mb']} MB)")
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (output_dir / "history.json").write_text(json.dumps({"head": history}, indent=2))


if __name__ == "__main__":
    main()
