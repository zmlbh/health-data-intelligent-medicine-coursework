"""Create the fixed, offline teaching split from sklearn's WDBC dataset."""
from pathlib import Path
import json
import platform

import pandas as pd
import sklearn
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split

BASE = Path(__file__).resolve().parents[1]
FEATURES = ["mean radius", "mean texture", "mean perimeter", "mean area", "mean smoothness",
            "mean compactness", "mean concavity", "mean concave points", "mean symmetry",
            "mean fractal dimension", "radius error", "texture error", "perimeter error",
            "area error", "smoothness error", "compactness error", "concavity error",
            "concave points error", "symmetry error", "fractal dimension error",
            "worst radius", "worst texture", "worst perimeter", "worst area", "worst smoothness",
            "worst compactness", "worst concavity", "worst concave points", "worst symmetry",
            "worst fractal dimension"]

def main():
    data = load_breast_cancer(as_frame=True)
    frame = data.frame.copy()
    frame.columns = FEATURES + ["target_raw"]
    frame.insert(0, "sample_id", [f"WDBC-{i:03d}" for i in range(1, len(frame) + 1)])
    # sklearn uses 0 for malignant and 1 for benign. The lesson uses malignant=1.
    frame["malignant"] = (frame["target_raw"] == 0).astype(int)
    dev, test = train_test_split(frame, test_size=114, stratify=frame.malignant, random_state=1010)
    train, validation = train_test_split(dev, test_size=114, stratify=dev.malignant, random_state=1010)
    student = BASE / "data" / "student"
    teacher = BASE / "data" / "teacher"
    student.mkdir(parents=True, exist_ok=True)
    teacher.mkdir(parents=True, exist_ok=True)
    keep = ["sample_id", *FEATURES, "malignant"]
    train[keep].to_csv(student / "train.csv", index=False)
    validation[keep].to_csv(student / "validation.csv", index=False)
    test[["sample_id", *FEATURES]].to_csv(student / "locked-test-features.csv", index=False)
    test[["sample_id", "malignant"]].to_csv(teacher / "locked-test-labels.csv", index=False)
    frame[["sample_id", *FEATURES, "malignant"]].to_csv(teacher / "all-measurements.csv", index=False)
    manifest = {
        "dataset": "Breast Cancer Wisconsin (Diagnostic), sklearn load_breast_cancer",
        "source": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "doi": "10.24432/C5DW2B", "seed": 1010, "positive_class": "malignant=1",
        "features": FEATURES, "splits": {},
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    for name, part in (("train", train), ("validation", validation), ("test", test)):
        manifest["splits"][name] = {"n": len(part), "class_counts": part.malignant.value_counts().sort_index().to_dict(),
                                     "sample_ids": part.sample_id.tolist()}
    (teacher / "split-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: v["class_counts"] for k, v in manifest["splits"].items()}, indent=2))

if __name__ == "__main__":
    main()
