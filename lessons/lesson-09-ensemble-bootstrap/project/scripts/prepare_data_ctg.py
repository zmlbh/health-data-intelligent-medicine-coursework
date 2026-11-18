"""Create the fixed, offline teaching split for the alternative CTG dataset (UCI Cardiotocography)."""
from pathlib import Path
import hashlib
import io
import json
import platform
import zipfile

import pandas as pd
import sklearn
from sklearn.model_selection import StratifiedGroupKFold

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data-ctg" / "raw" / "cardiotocography.zip"
SEED = 1010
# Counts in the raw sheet are converted to events per second, as in UCI's "Data" sheet.
RATE_COLUMNS = ["AC", "FM", "UC", "DL", "DS", "DP"]
FEATURES = ["LB", "AC", "FM", "UC", "DL", "DS", "DP", "ASTV", "MSTV", "ALTV", "MLTV", "Width", "Min", "Max",
            "Nmax", "Nzeros", "Mode", "Mean", "Median", "Variance", "Tendency"]

def load_raw():
    with zipfile.ZipFile(RAW) as archive:
        sheet = pd.read_excel(io.BytesIO(archive.read("CTG.xls")), sheet_name="Raw Data")
    frame = sheet.dropna(subset=["NSP"]).reset_index(drop=True)
    duration = frame["e"] - frame["b"]
    for column in RATE_COLUMNS:
        frame[column] = (frame[column] / duration).round(6)
    # One recording file holds several analysed segments; segments of one file must stay in one split.
    recordings = {name: f"REC-{i:03d}" for i, name in enumerate(pd.unique(frame["FileName"]), 1)}
    frame.insert(0, "recording_id", frame["FileName"].map(recordings))
    frame.insert(0, "sample_id", [f"CTG-{i:04d}" for i in range(1, len(frame) + 1)])
    frame["nsp_3class"] = frame["NSP"].astype(int)
    # Expert NSP: 1=normal, 2=suspect, 3=pathologic. The lesson uses pathologic=1 versus the rest.
    frame["pathologic"] = (frame["NSP"] == 3).astype(int)
    return frame

def group_split(frame, n_splits):
    folds = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    keep, hold = next(folds.split(frame, frame["pathologic"], frame["recording_id"]))
    return frame.iloc[keep], frame.iloc[hold]

def main():
    frame = load_raw()
    dev, test = group_split(frame, 5)
    train, validation = group_split(dev, 4)
    assert not set(train.recording_id) & set(validation.recording_id)
    assert not set(dev.recording_id) & set(test.recording_id)
    student = BASE / "data-ctg" / "student"
    teacher = BASE / "data-ctg" / "teacher"
    student.mkdir(parents=True, exist_ok=True)
    teacher.mkdir(parents=True, exist_ok=True)
    keep = ["sample_id", "recording_id", *FEATURES, "pathologic"]
    train[keep].to_csv(student / "train.csv", index=False)
    validation[keep].to_csv(student / "validation.csv", index=False)
    test[["sample_id", "recording_id", *FEATURES]].to_csv(student / "locked-test-features.csv", index=False)
    test[["sample_id", "pathologic", "nsp_3class"]].to_csv(teacher / "locked-test-labels.csv", index=False)
    frame[["sample_id", "recording_id", "FileName", "Date", "SegFile", "b", "e", *FEATURES, "CLASS",
           "nsp_3class", "pathologic"]].to_csv(teacher / "all-measurements.csv", index=False)
    manifest = {
        "dataset": "Cardiotocography (UCI id 193), sheet 'Raw Data' of CTG.xls",
        "source": "https://archive.ics.uci.edu/dataset/193/cardiotocography",
        "doi": "10.24432/C51S4N", "license": "CC BY 4.0",
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "seed": SEED, "positive_class": "pathologic=1 (NSP=3)", "group": "recording_id (raw FileName)",
        "features": FEATURES, "rate_columns_per_second": RATE_COLUMNS, "splits": {},
        "versions": {"python": platform.python_version(), "pandas": pd.__version__, "sklearn": sklearn.__version__},
    }
    for name, part in (("train", train), ("validation", validation), ("test", test)):
        manifest["splits"][name] = {"n": len(part), "n_recordings": int(part.recording_id.nunique()),
                                     "class_counts": part.pathologic.value_counts().sort_index().to_dict(),
                                     "sample_ids": part.sample_id.tolist()}
    (teacher / "split-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({k: {kk: v[kk] for kk in ("n", "n_recordings", "class_counts")} for k, v in manifest["splits"].items()}, indent=2))

if __name__ == "__main__":
    main()
