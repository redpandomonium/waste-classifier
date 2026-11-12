"""Dashboard for the waste classifier.

    streamlit run dashboard/app.py

Tabs: try a photo, train with your own settings, explore the confidence gate,
and browse the mistakes. Training here fits only the classifier head on cached
backbone features, so a run takes a few seconds on a laptop.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from waste_classifier.data import CLASS_NAMES, IMAGE_SIZE  # noqa: E402
from waste_classifier.evaluate import metrics_from_probabilities  # noqa: E402
from waste_classifier.features import available_backbones, load_feature_set  # noqa: E402

FEATURES_DIR = Path(os.environ.get("WASTE_FEATURES_DIR", ROOT / "outputs" / "features"))
OUTPUT_DIR = Path(os.environ.get("WASTE_OUTPUT_DIR", ROOT / "outputs"))
DATA_DIR = os.environ.get("WASTE_DATA_DIR", "")
MODELS_DIR = ROOT / "models"  # the model committed to the repo
TARGET = 0.90

st.set_page_config(page_title="Waste classifier", layout="wide")


def find_data_dir() -> Path | None:
    from waste_classifier.data import resolve_data_dir
    for candidate in (DATA_DIR, ROOT / "data", "~/Downloads/archive/DATASET"):
        if candidate:
            try:
                return resolve_data_dir(candidate)
            except FileNotFoundError:
                continue
    return None


@st.cache_resource(show_spinner="Loading cached features...")
def get_features(backbone: str):
    return load_feature_set(backbone, find_data_dir(), FEATURES_DIR)


@st.cache_resource(show_spinner="Loading the model...")
def get_tflite(path: str, modified: float):
    import tensorflow as tf
    try:
        from ai_edge_litert.interpreter import Interpreter
    except ImportError:
        Interpreter = tf.lite.Interpreter
    interpreter = Interpreter(model_path=path)
    interpreter.allocate_tensors()
    return interpreter


def current_model_dir() -> Path | None:
    """Your own saved model in outputs/ if there is one, else the committed one."""
    for folder in (OUTPUT_DIR, MODELS_DIR):
        if (folder / "waste_classifier.tflite").exists():
            return folder
    return None


def predict_photo(image) -> np.ndarray:
    import tensorflow as tf
    path = current_model_dir() / "waste_classifier.tflite"
    interpreter = get_tflite(str(path), path.stat().st_mtime)
    pixels = tf.image.resize(np.asarray(image.convert("RGB")), [IMAGE_SIZE, IMAGE_SIZE])
    batch = pixels.numpy()[None].astype(np.float32)
    interpreter.set_tensor(interpreter.get_input_details()[0]["index"], batch)
    interpreter.invoke()
    return interpreter.get_tensor(interpreter.get_output_details()[0]["index"])[0]


def show_metrics(metrics: dict, val_accuracy: float | None = None) -> None:
    columns = st.columns(4)
    accuracy = metrics["accuracy"]
    columns[0].metric("Test accuracy", f"{accuracy:.1%}",
                      f"{(accuracy - TARGET) * 100:+.1f} pts vs 90% target")
    if val_accuracy is not None:
        columns[1].metric("Validation accuracy", f"{val_accuracy:.1%}")
    columns[2].metric("Organic recall", f"{metrics['per_class']['Organic']['recall']:.1%}")
    columns[3].metric("Recyclable recall", f"{metrics['per_class']['Recyclable']['recall']:.1%}")


def confusion_table(metrics: dict) -> pd.DataFrame:
    return pd.DataFrame(metrics["confusion_matrix"],
                        index=[f"True {c}" for c in CLASS_NAMES],
                        columns=[f"Predicted {c}" for c in CLASS_NAMES])


st.title("Waste classifier")
st.caption("KTSustainability: Organic vs Recyclable")
ready = available_backbones(FEATURES_DIR)
tab_photo, tab_train, tab_gate, tab_mistakes = st.tabs(
    ["Try a photo", "Train", "Confidence gate", "Mistakes"])

# ---------------------------------------------------------------- Try a photo
with tab_photo:
    model_dir = current_model_dir()
    if model_dir is None:
        st.info("No exported model yet. Train one in the Train tab and save it, "
                "or run `python -m waste_classifier.head`.")
    else:
        model_path = model_dir / "waste_classifier.tflite"
        metrics_path = model_dir / "metrics.json"
        if metrics_path.exists():
            saved = json.loads(metrics_path.read_text())
            st.caption(f"Current model: {saved.get('backbone', 'unknown backbone')}, "
                       f"{saved['accuracy']:.1%} test accuracy, "
                       f"{model_path.stat().st_size / 1e6:.1f} MB TF Lite file")
        gate = st.slider("Confidence needed to accept the label", 0.50, 0.99, 0.90, 0.01,
                         key="photo_gate")
        upload = st.file_uploader("Photo of one item", type=["jpg", "jpeg", "png", "webp"])
        if upload:
            from PIL import Image
            image = Image.open(upload)
            probabilities = predict_photo(image)
            label = CLASS_NAMES[int(probabilities.argmax())]
            confidence = float(probabilities.max())
            left, right = st.columns([1, 1])
            left.image(image, width=360)
            right.metric("Label", label, f"{confidence:.1%} confident", delta_color="off")
            if confidence >= gate:
                right.success("Passes the confidence gate: the label would be accepted.")
            else:
                right.warning("Below the confidence gate: the app would ask for a retake.")
            right.bar_chart(pd.DataFrame({"Probability": probabilities}, index=CLASS_NAMES),
                            horizontal=True, height=160)

# ---------------------------------------------------------------------- Train
with tab_train:
    if not ready:
        st.warning(
            f"No cached features found in `{FEATURES_DIR}`. Create them once with "
            "`python eda/extract_features.py --data-dir <dataset folder> --backbone all` "
            "(about 10 minutes on a laptop), then reload this page.")
    else:
        with st.form("train"):
            st.subheader("Settings")
            c1, c2, c3, c4 = st.columns(4)
            default = ready.index("efficientnetv2b0") if "efficientnetv2b0" in ready else 0
            backbone = c1.selectbox("Backbone", ready, index=default)
            learning_rate = c2.select_slider(
                "Learning rate", [0.0001, 0.0003, 0.001, 0.003, 0.01], value=0.001)
            epochs = c3.slider("Max epochs", 1, 100, 30)
            batch_size = c4.select_slider("Batch size", [32, 64, 128, 256, 512], value=256)
            c5, c6, c7, c8 = st.columns(4)
            dropout = c5.slider("Dropout", 0.0, 0.8, 0.2, 0.05)
            l2 = c6.select_slider(
                "L2 weight decay", [0.0, 0.0001, 0.0003, 0.001, 0.003, 0.01, 0.03, 0.1], value=0.003)
            seed = c7.number_input("Random seed", 0, 9999, 1)
            class_weighting = c8.checkbox("Balance the classes", value=True)
            patience = c8.slider("Early-stopping patience", 1, 20, 5)
            submitted = st.form_submit_button("Train", type="primary")

        if submitted:
            from waste_classifier.head import train_head
            fs = get_features(backbone)
            start = time.time()
            with st.spinner("Training..."):
                head, history = train_head(
                    fs, learning_rate, epochs, batch_size, dropout, l2,
                    class_weighting, patience, int(seed))
                probabilities = head.predict(fs.x_test, verbose=0)
            metrics = metrics_from_probabilities(fs.y_test, probabilities)
            settings = {"backbone": backbone, "learning_rate": learning_rate, "epochs": epochs,
                        "batch_size": batch_size, "dropout": dropout, "l2": l2,
                        "seed": int(seed), "class_weighting": class_weighting,
                        "patience": patience}
            run = {"settings": settings, "metrics": metrics, "history": history,
                   "probabilities": probabilities, "labels": fs.y_test,
                   "paths": fs.test_paths, "head": head, "splits": fs.report,
                   "val_accuracy": max(history["val_accuracy"]),
                   "seconds": time.time() - start}
            st.session_state["run"] = run
            st.session_state.setdefault("runs", []).append({
                **settings, "epochs_run": len(history["loss"]),
                "val_accuracy": run["val_accuracy"], "test_accuracy": metrics["accuracy"],
                "organic_recall": metrics["per_class"]["Organic"]["recall"],
                "recyclable_recall": metrics["per_class"]["Recyclable"]["recall"]})

        run = st.session_state.get("run")
        if run:
            st.subheader("Latest run")
            st.caption(f"{run['settings']['backbone']}, trained in {run['seconds']:.1f} s, "
                       f"stopped after {len(run['history']['loss'])} epochs")
            show_metrics(run["metrics"], run["val_accuracy"])
            left, right = st.columns(2)
            curves = pd.DataFrame({
                "Train": run["history"]["accuracy"],
                "Validation": run["history"]["val_accuracy"]},
                index=pd.RangeIndex(1, len(run["history"]["loss"]) + 1, name="Epoch"))
            left.markdown("**Accuracy by epoch**")
            left.line_chart(curves, height=260)
            right.markdown("**Confusion matrix on TEST**")
            right.dataframe(confusion_table(run["metrics"]), width="stretch")

            if st.button("Save this run as the app model"):
                from waste_classifier.export_tflite import export
                from waste_classifier.head import assemble
                with st.spinner("Attaching the head to the backbone and exporting to TF Lite..."):
                    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    model = assemble(run["settings"]["backbone"], run["head"])
                    model.save(OUTPUT_DIR / "waste_classifier.keras")
                    tflite_path = export(model, OUTPUT_DIR)
                    saved = {**run["metrics"], "val_accuracy": run["val_accuracy"],
                             "backbone": run["settings"]["backbone"],
                             "settings": run["settings"], "splits": run["splits"],
                             "tflite_size_mb": round(tflite_path.stat().st_size / 1e6, 2)}
                    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(saved, indent=2))
                    (OUTPUT_DIR / "history.json").write_text(
                        json.dumps({"head": run["history"]}, indent=2))
                st.success(f"Saved {tflite_path.name} ({saved['tflite_size_mb']} MB) to {OUTPUT_DIR}")

        if st.session_state.get("runs"):
            st.subheader("Runs this session")
            table = pd.DataFrame(st.session_state["runs"])
            st.dataframe(
                table.style.format({"val_accuracy": "{:.2%}", "test_accuracy": "{:.2%}",
                                    "organic_recall": "{:.2%}", "recyclable_recall": "{:.2%}"}),
                width="stretch")
            st.caption("Choose settings by validation accuracy. Test accuracy is for reporting.")

# ------------------------------------------------------------ Confidence gate
with tab_gate:
    run = st.session_state.get("run")
    if not run:
        st.info("Train a model in the Train tab first.")
    else:
        probabilities, labels = run["probabilities"], run["labels"]
        confidence = probabilities.max(axis=1)
        correct = probabilities.argmax(axis=1) == labels
        gate = st.slider("Confidence threshold", 0.50, 0.99, 0.90, 0.01, key="gate")
        passed = confidence >= gate
        c1, c2, c3 = st.columns(3)
        c1.metric("Photos that pass", f"{passed.mean():.1%}")
        c2.metric("Accuracy on those", f"{correct[passed].mean():.1%}" if passed.any() else "n/a")
        c3.metric("Wrong answers that pass", f"{int((~correct & passed).sum())}",
                  f"of {int((~correct).sum())} errors", delta_color="off")
        thresholds = np.round(np.linspace(0.5, 0.99, 50), 2)
        curve = pd.DataFrame({
            "Accuracy on photos that pass (%)":
                [correct[confidence >= t].mean() * 100 for t in thresholds],
            "Share of photos that pass (%)":
                [(confidence >= t).mean() * 100 for t in thresholds]},
            index=pd.Index(thresholds, name="Confidence threshold"))
        st.line_chart(curve, height=320)
        st.caption("Measured on the published TEST images for the latest run.")

# -------------------------------------------------------------------- Mistakes
with tab_mistakes:
    run = st.session_state.get("run")
    data_dir = find_data_dir()
    if not run:
        st.info("Train a model in the Train tab first.")
    elif data_dir is None:
        st.info("Dataset folder not found. Set WASTE_DATA_DIR to browse the images.")
    else:
        probabilities, labels = run["probabilities"], run["labels"]
        predicted = probabilities.argmax(axis=1)
        confidence = probabilities.max(axis=1)
        wrong = np.where(predicted != labels)[0]
        which = st.radio("Show", ["All mistakes", "Recyclable called Organic",
                                  "Organic called Recyclable"], horizontal=True)
        if which == "Recyclable called Organic":
            wrong = wrong[labels[wrong] == 1]
        elif which == "Organic called Recyclable":
            wrong = wrong[labels[wrong] == 0]
        wrong = wrong[np.argsort(-confidence[wrong])]
        st.caption(f"{len(wrong)} test images, most confident first. Showing up to 24.")
        columns = st.columns(6)
        for position, i in enumerate(wrong[:24]):
            columns[position % 6].image(
                str(data_dir / run["paths"][i]),
                caption=f"said {CLASS_NAMES[predicted[i]]} ({confidence[i]:.0%})",
                width="stretch")
