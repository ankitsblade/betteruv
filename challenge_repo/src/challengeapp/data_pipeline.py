import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.feature_extraction.text import TfidfVectorizer


def build_dataframe() -> tuple[pd.DataFrame, float]:
    frame = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "text": ["alpha beta", "beta gamma", "gamma delta"],
            "value": [10.0, 20.0, 15.0],
        }
    )
    arr = np.asarray(frame["value"], dtype=float)
    mean_value = float(arr.mean())
    return frame, mean_value


def vectorize_text(frame: pd.DataFrame) -> tuple[int, int]:
    vec = TfidfVectorizer(min_df=1)
    matrix = vec.fit_transform(frame["text"])
    return matrix.shape


def local_sql_probe() -> str:
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        result = conn.execute(text("select 1")).scalar_one()
    return f"sqlite_probe={result}"
