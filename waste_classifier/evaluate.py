"""Score a trained model on the held-out TEST images.

    python -m waste_classifier.evaluate --model outputs/waste_classifier.keras \
        --data-dir ~/Downloads/archive/DATASET
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

from .data import CLASS_NAMES, build_splits, make_dataset


def metrics_from_probabilities(labels, probabilities) -> dict:
    """Accuracy, per-class precision/recall and confusion matrix."""
    probabilities = np.asarray(probabilities)
    predicted = probabilities.argmax(axis=1)
    y_true = np.asarray(labels)
    ids = list(range(len(CLASS_NAMES)))
    report = classification_report(
        y_true, predicted, labels=ids, target_names=CLASS_NAMES,
        output_dict=True, zero_division=0,
    )
    return {
        "test_images": int(len(y_true)),
        "accuracy": float((predicted == y_true).mean()),
        "per_class": {
            name: {k: float(report[name][k]) for k in ("precision", "recall", "f1-score")}
            for name in CLASS_NAMES
        },
        # Rows are the true class, columns the predicted class, in CLASS_NAMES order.
        "confusion_matrix": confusion_matrix(y_true, predicted, labels=ids).tolist(),
    }


def evaluate(model: tf.keras.Model, paths: list[str], labels: list[int],
             batch_size: int = 32) -> dict:
    ds = make_dataset(paths, labels, batch_size=batch_size, training=False)
    return metrics_from_probabilities(labels, model.predict(ds, verbose=0))


def print_metrics(metrics: dict) -> None:
    print(f"\nTest accuracy: {metrics['accuracy']:.4f} on {metrics['test_images']} images")
    for name, m in metrics["per_class"].items():
        print(f"  {name:<11} precision {m['precision']:.3f}  recall {m['recall']:.3f}")
    print("Confusion matrix (rows = true, columns = predicted):")
    for name, row in zip(CLASS_NAMES, metrics["confusion_matrix"]):
        print(f"  {name:<11} {row}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True)
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)
    splits = build_splits(args.data_dir)
    metrics = evaluate(model, *splits.test, batch_size=args.batch_size)
    print_metrics(metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
