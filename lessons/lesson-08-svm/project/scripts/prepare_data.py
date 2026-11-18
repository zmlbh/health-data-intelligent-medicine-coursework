"""Download the original UCI archive and create fixed teaching splits (offline thereafter)."""
from pathlib import Path
from io import StringIO
from zipfile import ZipFile
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
import pandas as pd
from sklearn.model_selection import train_test_split

BASE = Path(__file__).resolve().parents[1]
URL = 'https://archive.ics.uci.edu/static/public/212/vertebral+column.zip'
COLUMNS = ['pelvic_incidence', 'pelvic_tilt', 'lumbar_lordosis_angle',
           'sacral_slope', 'pelvic_radius', 'degree_spondylolisthesis', 'class_code']
FEATURES = ['pelvic_incidence', 'degree_spondylolisthesis']

def prepare(download=False):
    raw = BASE / 'data/raw/vertebral-column.zip'
    raw.parent.mkdir(parents=True, exist_ok=True)
    refreshed = download or not raw.exists()
    if refreshed:
        with urllib.request.urlopen(URL, timeout=60) as response:
            payload = response.read()
        with ZipFile(__import__('io').BytesIO(payload)) as archive:
            assert 'column_2C.dat' in archive.namelist(), archive.namelist()
        raw.write_bytes(payload)
    with ZipFile(raw) as archive:
        text = archive.read('column_2C.dat').decode('utf-8')
        dictionary = archive.read('column_2C_weka.arff').decode('utf-8', errors='replace').split('@data')[0]
    df = pd.read_csv(StringIO(text), sep=r'\s+', header=None, names=COLUMNS)
    assert len(df) == 310 and not df.isna().any().any()
    assert df.class_code.value_counts().to_dict() == {'AB': 210, 'NO': 100}
    df.insert(0, 'sample_id', [f'V{i:03d}' for i in range(1, 311)])
    df['abnormal'] = df.class_code.map({'AB': 1, 'NO': 0})
    dev, test = train_test_split(df, test_size=62, stratify=df.abnormal, random_state=9)
    train, val = train_test_split(dev, test_size=62, stratify=dev.abnormal, random_state=9)
    student = BASE / 'data/student'; teacher = BASE / 'data/teacher'
    student.mkdir(parents=True, exist_ok=True); teacher.mkdir(parents=True, exist_ok=True)
    for name, subset in [('train', train), ('validation', val)]:
        subset[['sample_id', *FEATURES, 'abnormal']].to_csv(student/f'{name}.csv', index=False)
    test[['sample_id', *FEATURES]].to_csv(student/'locked-test-features.csv', index=False)
    test[['sample_id', 'abnormal']].to_csv(teacher/'locked-test-labels.csv', index=False)
    df.to_csv(teacher/'all-measurements.csv', index=False)
    (BASE/'data/raw/field-definitions.txt').write_text(dictionary, encoding='utf-8')
    manifest_path = teacher/'split-manifest.json'
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    manifest = {'source': URL, 'doi': '10.24432/C5K89B', 'license': 'CC BY 4.0',
                'archive_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
                'downloaded_utc': (datetime.now(timezone.utc).isoformat() if refreshed
                                   else old.get('downloaded_utc', datetime.now(timezone.utc).isoformat())),
                'seed': 9, 'features': FEATURES, 'positive': 'AB',
                'splits': {name: {'n': len(sub), 'counts': sub.abnormal.value_counts().sort_index().to_dict(),
                                  'ids': sub.sample_id.tolist()}
                           for name, sub in [('train', train), ('validation', val), ('test', test)]},
                'versions': {'python': __import__('platform').python_version(),
                             'numpy': __import__('numpy').__version__, 'pandas': pd.__version__,
                             'sklearn': __import__('sklearn').__version__}}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print({name: value['counts'] for name, value in manifest['splits'].items()})
    print('SHA256', manifest['archive_sha256'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--download', action='store_true')
    prepare(parser.parse_args().download)
