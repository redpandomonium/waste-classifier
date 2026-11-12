"""Find the images, clean the splits, and turn them into tf.data pipelines.

Expected layout (the Kaggle "Waste Classification Data" archive):

    DATASET/
        TRAIN/O/*.jpg   TRAIN/R/*.jpg
        TEST/O/*.jpg    TEST/R/*.jpg
"""

from __future__ import annotations

import hashlib
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import tensorflow as tf
from sklearn.model_selection import train_test_split

IMAGE_SIZE = 224
# Folder name -> label index. The index order is the model's output order.
CLASS_DIRS = {"O": 0, "R": 1}
CLASS_NAMES = ["Organic", "Recyclable"]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


@dataclass
class Splits:
    train: tuple[list[str], list[int]]
    val: tuple[list[str], list[int]]
    test: tuple[list[str], list[int]]
    report: dict = field(default_factory=dict)


def resolve_data_dir(data_dir: str | Path) -> Path:
    """Return the folder that holds TRAIN/ and TEST/.

    The Kaggle archive nests DATASET/DATASET, and people point at either
    level, so walk down through DATASET folders until TRAIN shows up.
    """
    path = Path(data_dir).expanduser()
    for _ in range(3):
        if (path / "TRAIN").is_dir() and (path / "TEST").is_dir():
            return path
        if (path / "DATASET").is_dir():
            path = path / "DATASET"
        else:
            break
    raise FileNotFoundError(
        f"No TRAIN/ and TEST/ folders found under {Path(data_dir).expanduser()}"
    )


def list_images(split_dir: Path) -> tuple[list[str], list[int]]:
    paths, labels = [], []
    for folder, label in CLASS_DIRS.items():
        files = sorted(
            p for p in (split_dir / folder).iterdir()
            if p.suffix.lower() in IMAGE_SUFFIXES
        )
        paths += [str(p) for p in files]
        labels += [label] * len(files)
    return paths, labels


def _file_hash(path: str) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def build_splits(
    data_dir: str | Path,
    val_fraction: float = 0.1,
    seed: int = 42,
    limit_per_class: int | None = None,
) -> Splits:
    """Build clean train / validation / test splits.

    The raw archive has byte-identical images in both TRAIN and TEST, which
    would inflate test accuracy. This removes from TRAIN:
      * every image that also appears in TEST,
      * repeated copies of the same image (the first is kept),
      * images that appear under both labels (all copies dropped).
    TEST is left exactly as published.
    """
    root = resolve_data_dir(data_dir)
    train_paths, train_labels = list_images(root / "TRAIN")
    test_paths, test_labels = list_images(root / "TEST")

    test_hashes = {_file_hash(p) for p in test_paths}
    train_hashes = [_file_hash(p) for p in train_paths]

    labels_by_hash = defaultdict(set)
    for h, label in zip(train_hashes, train_labels):
        labels_by_hash[h].add(label)

    kept_paths, kept_labels, seen = [], [], set()
    dropped = Counter()
    for path, label, h in zip(train_paths, train_labels, train_hashes):
        if h in test_hashes:
            dropped["also_in_test"] += 1
        elif len(labels_by_hash[h]) > 1:
            dropped["conflicting_label"] += 1
        elif h in seen:
            dropped["repeated_in_train"] += 1
        else:
            seen.add(h)
            kept_paths.append(path)
            kept_labels.append(label)

    if limit_per_class:
        kept_paths, kept_labels = _limit(kept_paths, kept_labels, limit_per_class, seed)
        test_paths, test_labels = _limit(test_paths, test_labels, limit_per_class, seed)

    tr_p, va_p, tr_l, va_l = train_test_split(
        kept_paths, kept_labels,
        test_size=val_fraction, stratify=kept_labels, random_state=seed,
    )

    def counts(labels):
        c = Counter(labels)
        return {CLASS_NAMES[i]: c.get(i, 0) for i in range(len(CLASS_NAMES))}

    report = {
        "data_dir": str(root),
        "raw_train": len(train_paths),
        "dropped_from_train": dict(dropped),
        "train": counts(tr_l),
        "val": counts(va_l),
        "test": counts(test_labels),
    }
    return Splits((tr_p, tr_l), (va_p, va_l), (test_paths, test_labels), report)


def _limit(paths, labels, per_class, seed):
    """Random sample of up to `per_class` images per class (same every run)."""
    order = list(range(len(paths)))
    random.Random(seed).shuffle(order)
    paths, labels = [paths[i] for i in order], [labels[i] for i in order]
    out_p, out_l, taken = [], [], Counter()
    for p, l in zip(paths, labels):
        if taken[l] < per_class:
            taken[l] += 1
            out_p.append(p)
            out_l.append(l)
    return out_p, out_l


def load_image(path: tf.Tensor, label: tf.Tensor):
    """Decode one file to a 224x224x3 float image with values in [0, 255].

    Scaling to the range MobileNetV2 expects happens inside the model, so the
    app only has to do this same resize before calling the TF Lite model.
    """
    data = tf.io.read_file(path)
    # decode_image looks at the bytes, not the extension: some files in the
    # archive are PNGs named .jpg.
    image = tf.io.decode_image(data, channels=3, expand_animations=False)
    image = tf.image.resize(image, [IMAGE_SIZE, IMAGE_SIZE])
    image.set_shape([IMAGE_SIZE, IMAGE_SIZE, 3])
    return image, label


def augmentation() -> tf.keras.Sequential:
    """Training-only variation, aimed at messy real-world phone photos."""
    layers = tf.keras.layers
    return tf.keras.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomZoom(0.15),
            layers.RandomBrightness(0.2, value_range=(0, 255)),
            layers.RandomContrast(0.2),
        ],
        name="augmentation",
    )


def make_dataset(
    paths: list[str],
    labels: list[int],
    batch_size: int = 32,
    training: bool = False,
    seed: int = 42,
) -> tf.data.Dataset:
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        ds = ds.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)
    ds = ds.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(batch_size)
    if training:
        augment = augmentation()
        ds = ds.map(
            lambda x, y: (augment(x, training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE,
        )
    return ds.prefetch(tf.data.AUTOTUNE)


def class_weights(labels: list[int]) -> dict[int, float]:
    """Weights that make each class count equally despite the imbalance."""
    counts = Counter(labels)
    total, k = len(labels), len(counts)
    return {label: total / (k * n) for label, n in counts.items()}
