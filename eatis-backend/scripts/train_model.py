#!/usr/bin/env python
"""
scripts/train_model.py
────────────────────────
Standalone CLI to (re)train the XGBoost congestion prediction models.

Usage:
    python scripts/train_model.py --samples 5000

Models are saved to the MODEL_DIR configured in the environment
(defaults to ./models). The FastAPI app will load these on next startup,
or you can trigger a hot-reload via the predictor singleton.
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml.trainer import train_and_save

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train EATIS XGBoost congestion models")
    parser.add_argument("--samples", type=int, default=5000,
                       help="Number of synthetic training samples to generate (default: 5000)")
    args = parser.parse_args()

    logger.info("Starting model training with %d samples…", args.samples)
    metadata = train_and_save(n_samples=args.samples)

    logger.info("Training complete!")
    logger.info("  Model version:        %s", metadata["model_version"])
    logger.info("  Classifier accuracy:  %.2f%%", metadata["classifier_accuracy"] * 100)
    logger.info("  Trained at:           %s", metadata["trained_at"])


if __name__ == "__main__":
    main()
