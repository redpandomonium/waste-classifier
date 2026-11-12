# waste-classifier

Image classifier for KTSustainability, the sorting feature in the KTP Life app.
It labels a photo of an item as **Organic** or **Recyclable** and exports a
TensorFlow Lite model that runs on the phone.

The current model in `models/` is an EfficientNetV2-B0 backbone pretrained on
ImageNet with a trained two-class head. It scores **92.8%** on the 2,513
published test images (target: 90%).

## Layout

```
waste_classifier/     the Python package
    data.py           find images, clean the splits, build tf.data pipelines
    model.py          five pretrained backbones + classifier head
    features.py       load cached backbone features by split
    head.py           train only the head on cached features (seconds, no GPU)
    train.py          full training with fine-tuning (GPU recommended)
    evaluate.py       accuracy, precision/recall, confusion matrix
    export_tflite.py  Keras -> TF Lite, plus a Keras-vs-TF Lite check
dashboard/app.py      Streamlit dashboard
eda/                  dataset analysis and model comparison notebooks + figures
models/               the shared TF Lite model, labels and its metrics
notebooks/            Colab notebook for fine-tuning on a free GPU
Dockerfile, docker-compose.yml
```

## Quick start with Docker

Needs only Docker Desktop. From the repo folder:

```bash
docker compose up --build
```

Then open http://localhost:8501. The **Try a photo** tab works straight away
with the model in `models/`.

The other tabs need the dataset once, to cache features. Download the Kaggle
"Waste Classification Data" archive, then:

```bash
export WASTE_DATA_DIR=~/Downloads/archive/DATASET      # folder with TRAIN/ and TEST/
docker compose run --rm dashboard \
    python eda/extract_features.py --data-dir /data --backbone all
docker compose up
```

Feature extraction takes roughly 10 to 20 minutes on a laptop and is resumable.
The results land in `outputs/features/` on your machine, so it is a one-off.

## Quick start without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python eda/extract_features.py --data-dir ~/Downloads/archive/DATASET --backbone all
streamlit run dashboard/app.py
```

## The dashboard

| Tab | What it does |
| --- | --- |
| Try a photo | Upload a photo, see the label, the confidence, and whether it passes the confidence gate |
| Train | Pick a backbone, learning rate, epochs, batch size, dropout, L2, seed and class balancing; trains in seconds; compare runs; save one as the app model |
| Confidence gate | Move the threshold and see how many test photos pass and how accurate those are |
| Mistakes | Browse the test images the latest run got wrong |

"Save this run as the app model" writes `waste_classifier.tflite` and
`waste_classifier.keras` to `outputs/`. To share a new model with the team, copy
the `.tflite`, `labels.txt` and `metrics.json` from `outputs/` into `models/`
and commit them.

## Training from the command line

Head only, on cached features (what the dashboard does):

```bash
python -m waste_classifier.head --backbone efficientnetv2b0 --l2 0.0003
```

Full training with fine-tuning of the backbone (use a GPU; see
`notebooks/train_colab.ipynb`):

```bash
python -m waste_classifier.train --data-dir ~/Downloads/archive/DATASET --backbone mobilenetv2
```

Backbones: `mobilenetv2`, `mobilenetv3small`, `mobilenetv3large`,
`efficientnetb0`, `efficientnetv2b0`.

## Using the TF Lite model in the app

- **Input:** one image, shape `[1, 224, 224, 3]`, `float32`, RGB, values 0-255.
  Resize the photo to 224x224 with bilinear interpolation. Do not divide by
  255: scaling is built into the model.
- **Output:** `[P(Organic), P(Recyclable)]`, summing to 1. The larger value is
  the label and its value is the confidence score.

## EDA and model comparison

`eda/01_dataset_eda.ipynb` and `eda/02_model_comparison.ipynb` hold the code
and results; the figures are saved in `eda/figures/`. To rerun them:

```bash
pip install -r requirements-eda.txt
export WASTE_DATA_DIR=~/Downloads/archive/DATASET
jupyter lab eda/
```

Main findings:

- 285 training images are byte-identical to test images (20% of the Organic
  test images). They are removed from training so test accuracy is not inflated.
  40 more repeat within training, and one image appears under both labels.
- TEST is not distributed like TRAIN: Recyclable test images have about half the
  white-background share of Recyclable training images.
- Four of five pretrained backbones clear 90% with only the head trained.
- The errors that remain are mostly Recyclable items labelled Organic, often
  brightly coloured ones such as paper flowers and straws.

## How the data is cleaned

The raw archive is used as published, with three fixes applied to TRAIN only:
images that also appear in TEST are removed, repeated images are kept once, and
images that appear under both labels are dropped. 10% of the remaining training
images are held out for validation. TEST is never used to choose settings. The
Kaggle archive also contains a second full copy of everything under
`DATASET/DATASET/`; it is ignored.
