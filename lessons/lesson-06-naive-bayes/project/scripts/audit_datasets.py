"""Audit official local archives without fitting models; output goes to project .tmp."""

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd


def main():
    lesson = Path(__file__).resolve().parents[1]
    project = lesson.parents[2]
    raw = lesson / "data" / "raw"
    acute_path = raw / "acute+inflammations.zip"
    diabetes_path = raw / "early+stage+diabetes+risk+prediction+dataset.zip"
    names = [
        "temperature_c", "nausea", "lumbar_pain", "urine_pushing",
        "micturition_pain", "burning_urethra", "bladder_inflammation", "nephritis",
    ]
    with ZipFile(acute_path) as archive:
        with archive.open("diagnosis.data") as source:
            acute = pd.read_csv(
                source, sep="\t", encoding="utf-16", decimal=",", header=None, names=names
            )
    with ZipFile(diabetes_path) as archive:
        with archive.open("diabetes_data_upload.csv") as source:
            diabetes = pd.read_csv(source)

    binary = acute[names[1:6]].apply(lambda s: s.map({"yes": 1, "no": 0}))
    binary.insert(0, "fever_ge_38", (acute.temperature_c >= 38).astype(int))
    symptoms = diabetes.drop(columns=["Age", "Gender", "class"])
    mapped = symptoms.apply(lambda s: s.map({"Yes": 1, "No": 0}))
    assert acute.shape == (120, 8) and diabetes.shape == (520, 17)
    assert not binary.isna().any().any() and not mapped.isna().any().any()

    def summary(frame):
        return {
            "shape": list(frame.shape),
            "missing_cells": int(frame.isna().sum().sum()),
            "duplicate_extra_rows": int(frame.duplicated().sum()),
            "unique_complete_rows": len(frame.drop_duplicates()),
        }

    report = {
        "acute": {
            **summary(acute),
            "bladder_counts": acute.bladder_inflammation.value_counts().to_dict(),
            "nephritis_counts": acute.nephritis.value_counts().to_dict(),
            "unique_binary_feature_profiles": len(binary.drop_duplicates()),
        },
        "diabetes": {
            **summary(diabetes),
            "label_counts": diabetes["class"].value_counts().to_dict(),
            "age_range": [int(diabetes.Age.min()), int(diabetes.Age.max())],
            "duplicate_extra_input_rows": int(diabetes.drop(columns="class").duplicated().sum()),
            "unique_symptom_profiles": len(symptoms.drop_duplicates()),
        },
        "archive_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [acute_path, diabetes_path]
        },
    }
    target = project / ".tmp" / "naive-bayes-dataset-search" / "audit.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    target.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"Report: {target}")


if __name__ == "__main__":
    main()
