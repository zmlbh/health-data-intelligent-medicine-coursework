"""Teacher checks for the linear-model lesson. Outputs belong in .tmp/linear-models."""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split
BASE=Path(__file__).resolve().parents[1]
df=pd.read_csv(BASE/'data'/'heart.csv')
out=Path.cwd()/'.tmp'/'linear-models'; out.mkdir(parents=True,exist_ok=True)
summary={'rows':len(df),'positive':int(df.heart_disease_present.sum()),'negative':int((1-df.heart_disease_present).sum())}
pd.Series(summary).to_json(out/'data-summary.json',force_ascii=False)
print(summary)
