"""Public UCI Online Retail dataset loader with local cache and upload fallback."""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
CACHE = DATA_DIR / "online_retail.csv"
DATASET_URL = "https://archive.ics.uci.edu/dataset/352/online+retail"


def load_public_dataset() -> tuple[pd.DataFrame, str]:
    DATA_DIR.mkdir(exist_ok=True)
    if CACHE.exists():
        return pd.read_csv(CACHE, low_memory=False), f"Cached UCI Online Retail CSV ({CACHE.name})"
    try:
        from ucimlrepo import fetch_ucirepo
        dataset = fetch_ucirepo(id=352)
        features = dataset.data.features
        targets = dataset.data.targets
        df = pd.concat([features, targets], axis=1) if targets is not None and len(targets.columns) else features.copy()
        df.to_csv(CACHE, index=False)
        return df, "Downloaded from UCI Machine Learning Repository (dataset 352)"
    except Exception as exc:
        raise RuntimeError(f"Could not download UCI dataset. Check internet access or upload its CSV manually. Source: {DATASET_URL}. Details: {exc}") from exc
