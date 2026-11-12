"""Cache frozen-backbone features for every image, so models can be compared fast.

    python eda/extract_features.py --data-dir ~/Downloads/archive/DATASET \\
        --backbone all

Each backbone gets a file outputs/features/<backbone>.npy with one row per image,
in the order listed in outputs/features/index.json. The run is resumable: stop it
(or pass --max-seconds) and start it again to continue where it left off.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import tensorflow as tf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from waste_classifier.data import list_images, load_image, resolve_data_dir  # noqa: E402
from waste_classifier.model import BACKBONES, build_feature_extractor  # noqa: E402


def build_index(root: Path) -> list[dict]:
    rows = []
    for split in ("TRAIN", "TEST"):
        paths, labels = list_images(root / split)
        rows += [
            {"path": str(Path(p).relative_to(root)), "split": split, "label": l}
            for p, l in zip(paths, labels)
        ]
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--backbone", choices=sorted(BACKBONES) + ["all"], required=True)
    parser.add_argument("--out-dir", default="outputs/features")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--flip", action="store_true",
                        help="Extract features of the mirrored images instead")
    parser.add_argument("--max-seconds", type=float, default=None,
                        help="Stop cleanly after this long; rerun to continue")
    args = parser.parse_args()
    start = time.time()

    root = resolve_data_dir(args.data_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    index_path = out_dir / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text())
    else:
        index = build_index(root)
        index_path.write_text(json.dumps(index))

    backbones = sorted(BACKBONES) if args.backbone == "all" else [args.backbone]
    for backbone in backbones:
        if args.max_seconds and time.time() - start > args.max_seconds:
            break
        extract(backbone, args, root, index, out_dir, start)


def extract(backbone, args, root, index, out_dir, start) -> None:
    name = backbone + ("_flip" if args.flip else "")
    feature_path = out_dir / f"{name}.npy"
    progress_path = out_dir / f"{name}.progress"
    done = int(progress_path.read_text()) if progress_path.exists() else 0
    if done >= len(index):
        print(f"{name}: already complete ({done} images)")
        return

    model = build_feature_extractor(backbone)
    dim = model.output_shape[-1]
    if feature_path.exists() and done > 0:
        features = np.lib.format.open_memmap(feature_path, mode="r+")
    else:
        features = np.lib.format.open_memmap(
            feature_path, mode="w+", dtype=np.float16, shape=(len(index), dim))
        done = 0

    paths = [str(root / row["path"]) for row in index[done:]]
    ds = tf.data.Dataset.from_tensor_slices((paths, [0] * len(paths)))
    ds = ds.map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
    ds = ds.batch(args.batch_size).prefetch(tf.data.AUTOTUNE)

    for i, (images, _) in enumerate(ds):
        if args.flip:
            images = tf.image.flip_left_right(images)
        # predict_on_batch runs as a graph, which needs far less memory than an eager call.
        batch = model.predict_on_batch(images)
        features[done:done + len(batch)] = batch
        done += len(batch)
        if i % 10 == 9 or done >= len(index):
            features.flush()
            progress_path.write_text(str(done))
        if args.max_seconds and time.time() - start > args.max_seconds:
            break

    features.flush()
    progress_path.write_text(str(done))
    state = "complete" if done >= len(index) else "paused"
    print(f"{name}: {done}/{len(index)} images, {dim} features, {state}, "
          f"{time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
