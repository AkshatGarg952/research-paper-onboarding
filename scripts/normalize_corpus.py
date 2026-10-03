"""
Execution script to run corpus normalization.
Processes data/raw/papers_raw.json and outputs data/processed/papers.jsonl.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from research_onboarding.normalization import CorpusNormalizer


def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_path = base_dir / "data" / "raw" / "papers_raw.json"
    processed_path = base_dir / "data" / "processed" / "papers.jsonl"

    print("Starting corpus normalization...")
    print(f"Reading from: {raw_path}")
    print(f"Target destination: {processed_path}")

    normalizer = CorpusNormalizer(raw_path)
    stats = normalizer.export_jsonl(processed_path)

    print("\nNormalization complete:")
    for k, v in stats.items():
        print(f"  - {k}: {v}")

    print(f"\nSuccessfully generated {processed_path}")


if __name__ == "__main__":
    main()
