"""Prepare fixed teaching splits from the unmodified UCI archive."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from zipfile import ZipFile
import json
import hashlib
import pandas as pd
from sklearn.model_selection import train_test_split
from lab_utils import FEATURES

BASE = Path(__file__).resolve().parents[1]

def main():
    names = ['temperature_c', *FEATURES[1:], 'bladder_inflammation', 'nephritis']
    archive = BASE/'data/raw/acute+inflammations.zip'
    with ZipFile(archive) as z:
        with z.open('diagnosis.data') as source:
            original = pd.read_csv(source, sep='\t', encoding='utf-16', decimal=',',
                                   names=names, header=None)
    binary = original.copy()
    for name in names[1:]:
        binary[name] = original[name].map({'yes': 1, 'no': 0})
    binary.insert(0, 'sample_id', [f'A{i+1:03d}' for i in range(len(binary))])
    binary.insert(2, 'fever_ge_38', (binary.temperature_c >= 38).astype(int))
    assert not binary.isna().any().any()
    dev, test = train_test_split(binary.index, test_size=.2,
                                stratify=binary.bladder_inflammation, random_state=7)
    train, validation = train_test_split(dev, test_size=.25,
                                        stratify=binary.loc[dev, 'bladder_inflammation'],
                                        random_state=7)
    student, teacher = BASE/'data/student', BASE/'data/teacher'
    student.mkdir(parents=True, exist_ok=True)
    teacher.mkdir(parents=True, exist_ok=True)
    split = {}
    for name, idx in [('train', train), ('validation', validation), ('test', test)]:
        part = binary.loc[idx].copy()
        split[name] = part.sample_id.tolist()
        if name == 'test':
            part[['sample_id', 'temperature_c', *FEATURES]].to_csv(
                student/'locked-test-features.csv', index=False)
            part[['sample_id', 'bladder_inflammation', 'nephritis']].to_csv(
                teacher/'locked-test-labels.csv', index=False)
        else:
            part.to_csv(student/f'{name}.csv', index=False)
    (teacher/'split-manifest.json').write_text(json.dumps({
        'seed': 7, 'stratify': 'bladder_inflammation',
        'procedure': 'test_size=.2, then validation_size=.25 of development',
        'source_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
        'sample_ids': split}, indent=2)+'\n', encoding='utf-8')
    print('Prepared train/validation/test: 72/24/24; labels kept in data/teacher.')

if __name__ == '__main__':
    main()
