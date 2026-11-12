"""Load cached backbone features (written by eda/extract_features.py) by split."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .data import build_splits, resolve_data_dir

DEFAULT_FEATURES_DIR = "outputs/features"


@dataclass
class FeatureSet:
    backbone: str
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray
    test_paths: list[str]  # relative to the dataset folder
    report: dict


def available_backbones(features_dir: str | Path = DEFAULT_FEATURES_DIR) -> list[str]:
    """Backbones whose feature file is complete."""
    features_dir = Path(features_dir)
    index_path = features_dir / "index.json"
    if not index_path.exists():
        return []
    total = len(json.loads(index_path.read_text()))
    names = []
    for progress in sorted(features_dir.glob("*.progress")):
        if "_flip" not in progress.stem and int(progress.read_text()) >= total:
            names.append(progress.stem)
    return names


def split_rows(features_dir: str | Path, data_dir: str | Path | None,
               val_fraction: float = 0.1, seed: int = 42) -> dict:
    """Row numbers of the cleaned train / val / test splits in the feature files.

    The answer is cached next to the features, so once it exists the dataset
    itself is no longer needed to train or compare classifier heads.
    """
    features_dir = Path(features_dir)
    cache = features_dir / f"splits_seed{seed}_val{val_fraction}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    if data_dir is None:
        raise FileNotFoundError(
            f"{cache} does not exist yet; pass the dataset folder once to create it")

    root = resolve_data_dir(data_dir)
    index = json.loads((features_dir / "index.json").read_text())
    row_of = {row["path"]: i for i, row in enumerate(index)}
    splits = build_splits(root, val_fraction, seed)

    def rows(paths):
        return [row_of[str(Path(p).relative_to(root))] for p in paths]

    result = {
        "train": rows(splits.train[0]), "val": rows(splits.val[0]),
        "test": rows(splits.test[0]), "report": splits.report,
    }
    cache.write_text(json.dumps(result))
    return result


def load_feature_set(backbone: str, data_dir: str | Path | None = None,
                     features_dir: str | Path = DEFAULT_FEATURES_DIR,
                     val_fraction: float = 0.1, seed: int = 42) -> FeatureSet:
    features_dir = Path(features_dir)
    index = json.loads((features_dir / "index.json").read_text())
    labels = np.array([row["label"] for row in index])
    features = np.load(features_dir / f"{backbone}.npy", mmap_mode="r")
    rows = split_rows(features_dir, data_dir, val_fraction, seed)

    def take(name):
        idx = np.array(rows[name])
        return np.asarray(features[np.sort(idx)], dtype=np.float32), labels[np.sort(idx)], np.sort(idx)

    x_train, y_train, _ = take("train")
    x_val, y_val, _ = take("val")
    x_test, y_test, test_idx = take("test")
    return FeatureSet(backbone, x_train, y_train, x_val, y_val, x_test, y_test,
                      [index[i]["path"] for i in test_idx], rows["report"])
