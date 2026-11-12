"""Convert the trained Keras model to TensorFlow Lite for the app.

    python -m waste_classifier.export_tflite --model outputs/waste_classifier.keras

Writes waste_classifier.tflite and labels.txt next to the Keras model.
The TF Lite model takes one 224x224x3 float32 image with values in [0, 255]
and returns [P(Organic), P(Recyclable)].
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import tensorflow as tf

from .data import CLASS_NAMES, IMAGE_SIZE


QUANTIZE_CHOICES = ("float16", "none", "dynamic")


def export(model: tf.keras.Model, output_dir: str | Path,
           quantize: str = "float16") -> Path:
    """Write waste_classifier.tflite and labels.txt.

    quantize:
      "float16" (default) halves the file (about 4.5 MB) and matches Keras closely.
      "none"    keeps float32 weights (about 9 MB), identical to Keras.
      "dynamic" is smallest (about 2.5 MB) but shifts probabilities noticeably,
                which matters because the app gates on a confidence threshold.
    """
    if quantize not in QUANTIZE_CHOICES:
        raise ValueError(f"quantize must be one of {QUANTIZE_CHOICES}")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    if quantize != "none":
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    if quantize == "float16":
        converter.target_spec.supported_types = [tf.float16]
    tflite_bytes = converter.convert()

    tflite_path = output_dir / "waste_classifier.tflite"
    tflite_path.write_bytes(tflite_bytes)
    (output_dir / "labels.txt").write_text("\n".join(CLASS_NAMES) + "\n")
    return tflite_path


def run_tflite(tflite_path: str | Path, images: np.ndarray) -> np.ndarray:
    """Run the TF Lite model on a batch of [0, 255] float images, one at a time."""
    try:  # LiteRT is the successor to tf.lite.Interpreter; use it when installed.
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        Interpreter = tf.lite.Interpreter
    interpreter = Interpreter(model_path=str(tflite_path))
    interpreter.allocate_tensors()
    input_index = interpreter.get_input_details()[0]["index"]
    output_index = interpreter.get_output_details()[0]["index"]
    outputs = []
    for image in images:
        interpreter.set_tensor(input_index, image[None].astype(np.float32))
        interpreter.invoke()
        outputs.append(interpreter.get_tensor(output_index)[0])
    return np.array(outputs)


def check_against_keras(model: tf.keras.Model, tflite_path: str | Path,
                        images: np.ndarray) -> dict:
    """Compare TF Lite and Keras predictions on the same images."""
    keras_out = model.predict(images, verbose=0)
    lite_out = run_tflite(tflite_path, images)
    return {
        "images_checked": int(len(images)),
        "same_label": float((keras_out.argmax(1) == lite_out.argmax(1)).mean()),
        "max_probability_gap": float(np.abs(keras_out - lite_out).max()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--quantize", choices=QUANTIZE_CHOICES, default="float16")
    args = parser.parse_args()

    model = tf.keras.models.load_model(args.model)
    output_dir = args.output_dir or Path(args.model).parent
    path = export(model, output_dir, quantize=args.quantize)
    print(f"Wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")

    noise = np.random.default_rng(0).uniform(0, 255, (8, IMAGE_SIZE, IMAGE_SIZE, 3))
    print("Keras vs TF Lite on random inputs:", check_against_keras(model, path, noise))


if __name__ == "__main__":
    main()
