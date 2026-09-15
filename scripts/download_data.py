"""Download the raw dataset from Kaggle and place it under data/raw/.

The repository ships the dataset (data/raw/hotel_reservations.csv) so a fresh
clone works out of the box. This script re-downloads the original source for
full reproducibility.

Usage:
    python scripts/download_data.py
"""

from pathlib import Path

import kagglehub

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "hotel_reservations.csv"
SOURCE_FILE = "Hotel Reservations.csv"


def main() -> None:
    path = Path(
        kagglehub.dataset_download("ahsan81/hotel-reservations-classification-dataset")
    )
    src = path / SOURCE_FILE
    if not src.exists():
        raise FileNotFoundError(
            f"{SOURCE_FILE} not found in downloaded dataset: {path}"
        )
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_bytes(src.read_bytes())
    print(f"Dataset saved to {DEST}")


if __name__ == "__main__":
    main()
