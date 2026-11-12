"""Train the waste classifier, score it on TEST, and export it to TF Lite.

    python -m waste_classifier.train --data-dir ~/Downloads/archive/DATASET

Two stages: first only the new classifier head is trained on top of a frozen
ImageNet MobileNetV2, then the top of the backbone is unfrozen and fine-tuned
at a low learning rate. Everything is written to --output-dir.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf

from .data import build_splits, class_weights, make_dataset
from .evaluate import evaluate, print_metrics
from .export_tflite import check_against_keras, export
from .model import BACKBONES, DEFAULT_BACKBONE, build_model, compile_model, unfreeze_top


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", required=True,
                        help="Folder containing TRAIN/ and TEST/ (or its parent)")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--epochs", type=int, default=8,
                        help="Epochs for the head with the backbone frozen")
    parser.add_argument("--fine-tune-epochs", type=int, default=6,
                        help="Extra epochs with the top of the backbone unfrozen")
    parser.add_argument("--fine-tune-layers", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--backbone", choices=sorted(BACKBONES), default=DEFAULT_BACKBONE)
    parser.add_argument("--no-pretrained", action="store_true",
                        help="Start from random weights (only useful for quick tests)")
    parser.add_argument("--limit-per-class", type=int, default=None,
                        help="Use only this many images per class (quick tests)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    splits = build_splits(args.data_dir, args.val_fraction, args.seed,
                          args.limit_per_class)
    print(json.dumps(splits.report, indent=2))

    train_ds = make_dataset(*splits.train, batch_size=args.batch_size,
                            training=True, seed=args.seed)
    val_ds = make_dataset(*splits.val, batch_size=args.batch_size)
    weights = class_weights(splits.train[1])

    model = build_model(weights=None if args.no_pretrained else "imagenet",
                        backbone=args.backbone)
    best_path = output_dir / "waste_classifier.keras"

    def callbacks():
        return [
            tf.keras.callbacks.ModelCheckpoint(
                str(best_path), monitor="val_accuracy", save_best_only=True),
            tf.keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=3, restore_best_weights=True),
        ]

    history = {}

    print("\nStage 1: training the classifier head")
    compile_model(model, learning_rate=1e-3)
    h = model.fit(train_ds, validation_data=val_ds, epochs=args.epochs,
                  class_weight=weights, callbacks=callbacks())
    history["head"] = h.history

    if args.fine_tune_epochs > 0:
        print("\nStage 2: fine-tuning the top of the backbone")
        unfreeze_top(model, args.fine_tune_layers)
        compile_model(model, learning_rate=1e-5)
        h = model.fit(train_ds, validation_data=val_ds, epochs=args.fine_tune_epochs,
                      class_weight=weights, callbacks=callbacks())
        history["fine_tune"] = h.history

    # Keep whichever epoch scored best on validation across both stages.
    model = tf.keras.models.load_model(best_path)

    metrics = evaluate(model, *splits.test, batch_size=args.batch_size)
    print_metrics(metrics)

    tflite_path = export(model, output_dir)
    # Spread the comparison sample across the test set so both classes are in it.
    step = max(1, len(splits.test[0]) // 100)
    sample = make_dataset(splits.test[0][::step], splits.test[1][::step],
                          batch_size=args.batch_size)
    images = np.concatenate([batch.numpy() for batch, _ in sample])
    metrics["tflite_check"] = check_against_keras(model, tflite_path, images)
    metrics["tflite_size_mb"] = round(tflite_path.stat().st_size / 1e6, 2)
    metrics["splits"] = splits.report
    metrics["backbone"] = args.backbone

    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (output_dir / "history.json").write_text(json.dumps(
        {stage: {k: [float(v) for v in vals] for k, vals in hist.items()}
         for stage, hist in history.items()}, indent=2))

    print(f"\nTF Lite model: {tflite_path} ({metrics['tflite_size_mb']} MB)")
    print("Keras vs TF Lite on test images:", metrics["tflite_check"])
    print(f"Saved model, metrics.json and history.json to {output_dir}/")


if __name__ == "__main__":
    main()
