#!/usr/bin/env python3
"""
High-Resolution Dataset Generation Script for 3SA AI Anomaly Detector

Generates synthetic handshake data with literature-based parameters:
- Exact byte sizes (ML-KEM-768: 1184/1088, ML-KEM-1024: 1568/1568, Classical: 32/32)
- Sub-millisecond timing (0.50-0.70ms for PQC, 0.1-0.5ms for classical)
- Anomaly injection (timing attacks, size tampering, implicit rejection)
- High-resolution logging with nanosecond precision
"""

import time
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
from pathlib import Path
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[dataset] %(levelname)s: %(message)s"
)
_LOGGER = logging.getLogger("dataset")


class DatasetGenerator:
    """Generate synthetic handshake datasets for AI anomaly detector training."""

    # Literature-based exact sizes
    SIZES = {
        "ML-KEM-768": {"public_key": 1184, "ciphertext": 1088},
        "ML-KEM-1024": {"public_key": 1568, "ciphertext": 1568},
        "Classical": {"public_key": 32, "ciphertext": 32},
    }

    # Literature-based timing parameters (in nanoseconds)
    TIMING = {
        "ML-KEM-768": {"min": 500_000, "max": 700_000, "threshold": 2_000_000},
        "ML-KEM-1024": {"min": 500_000, "max": 700_000, "threshold": 2_000_000},
        "Classical": {"min": 100_000, "max": 500_000, "threshold": 1_000_000},
    }

    def __init__(self, output_dir: str = "datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dataset = []

    def generate_normal_handshake(
        self,
        suite: str,
        count: int = 100
    ) -> List[Dict]:
        """Generate normal handshake data within expected parameters."""
        _LOGGER.info(f"Generating {count} normal handshakes for {suite}...")
        
        sizes = self.SIZES[suite]
        timing = self.TIMING[suite]
        samples = []

        for i in range(count):
            # Generate latency within expected range (normal distribution)
            latency_ns = np.random.normal(
                loc=(timing["min"] + timing["max"]) / 2,
                scale=(timing["max"] - timing["min"]) / 6,
            )
            latency_ns = np.clip(latency_ns, timing["min"], timing["max"])
            latency_ms = latency_ns / 1_000_000

            # Exact sizes (literature: PQC sizes are mathematically fixed)
            ciphertext_size = sizes["ciphertext"]
            public_key_size = sizes["public_key"]

            sample = {
                "iteration": i,
                "suite": suite,
                "latency_ms": latency_ms,
                "latency_ns": latency_ns,
                "ciphertext_size": ciphertext_size,
                "public_key_size": public_key_size,
                "success": True,
                "encap_variance": 0.0,
                "label": 0,  # Normal
                "anomaly_type": "normal",
            }
            samples.append(sample)

        return samples

    def generate_timing_anomaly(
        self,
        suite: str,
        count: int = 50,
        severity: str = "moderate"
    ) -> List[Dict]:
        """Generate timing-based anomalies (side-channel attacks)."""
        _LOGGER.info(f"Generating {count} timing anomalies for {suite} ({severity})...")
        
        sizes = self.SIZES[suite]
        timing = self.TIMING[suite]
        samples = []

        # Severity multipliers
        severity_map = {
            "mild": 3.0,      # 3x threshold
            "moderate": 10.0,  # 10x threshold
            "severe": 50.0,   # 50x threshold
        }
        multiplier = severity_map.get(severity, 10.0)

        for i in range(count):
            # Latency exceeding threshold (severe anomaly)
            latency_ns = timing["threshold"] * multiplier * np.random.uniform(0.8, 1.2)
            latency_ms = latency_ns / 1_000_000

            # Exact sizes (timing attack doesn't change sizes)
            ciphertext_size = sizes["ciphertext"]
            public_key_size = sizes["public_key"]

            sample = {
                "iteration": i,
                "suite": suite,
                "latency_ms": latency_ms,
                "latency_ns": latency_ns,
                "ciphertext_size": ciphertext_size,
                "public_key_size": public_key_size,
                "success": True,
                "encap_variance": 0.0,
                "label": 1,  # Anomalous
                "anomaly_type": f"timing_{severity}",
            }
            samples.append(sample)

        return samples

    def generate_size_anomaly(
        self,
        suite: str,
        count: int = 50,
        anomaly_type: str = "ciphertext_tampering"
    ) -> List[Dict]:
        """Generate size-based anomalies (ciphertext/public key tampering)."""
        _LOGGER.info(f"Generating {count} size anomalies for {suite} ({anomaly_type})...")
        
        sizes = self.SIZES[suite]
        timing = self.TIMING[suite]
        samples = []

        for i in range(count):
            # Normal latency (size anomaly doesn't affect timing)
            latency_ns = np.random.normal(
                loc=(timing["min"] + timing["max"]) / 2,
                scale=(timing["max"] - timing["min"]) / 6,
            )
            latency_ns = np.clip(latency_ns, timing["min"], timing["max"])
            latency_ms = latency_ns / 1_000_000

            # Tampered sizes (any deviation is anomalous)
            if anomaly_type == "ciphertext_tampering":
                ciphertext_size = sizes["ciphertext"] + np.random.randint(-100, 100)
                public_key_size = sizes["public_key"]
            elif anomaly_type == "public_key_tampering":
                ciphertext_size = sizes["ciphertext"]
                public_key_size = sizes["public_key"] + np.random.randint(-100, 100)
            else:  # both_tampering
                ciphertext_size = sizes["ciphertext"] + np.random.randint(-100, 100)
                public_key_size = sizes["public_key"] + np.random.randint(-100, 100)

            sample = {
                "iteration": i,
                "suite": suite,
                "latency_ms": latency_ms,
                "latency_ns": latency_ns,
                "ciphertext_size": ciphertext_size,
                "public_key_size": public_key_size,
                "success": True,
                "encap_variance": 0.0,
                "label": 1,  # Anomalous
                "anomaly_type": anomaly_type,
            }
            samples.append(sample)

        return samples

    def generate_implicit_rejection(
        self,
        suite: str,
        count: int = 30
    ) -> List[Dict]:
        """Generate implicit rejection failures (ciphertext manipulation)."""
        _LOGGER.info(f"Generating {count} implicit rejection failures for {suite}...")
        
        sizes = self.SIZES[suite]
        timing = self.TIMING[suite]
        samples = []

        for i in range(count):
            # Normal latency (implicit rejection is silent)
            latency_ns = np.random.normal(
                loc=(timing["min"] + timing["max"]) / 2,
                scale=(timing["max"] - timing["min"]) / 6,
            )
            latency_ns = np.clip(latency_ns, timing["min"], timing["max"])
            latency_ms = latency_ns / 1_000_000

            # Exact sizes (implicit rejection happens after size validation)
            ciphertext_size = sizes["ciphertext"]
            public_key_size = sizes["public_key"]

            sample = {
                "iteration": i,
                "suite": suite,
                "latency_ms": latency_ms,
                "latency_ns": latency_ns,
                "ciphertext_size": ciphertext_size,
                "public_key_size": public_key_size,
                "success": False,  # Failure due to implicit rejection
                "encap_variance": 0.0,
                "label": 1,  # Anomalous
                "anomaly_type": "implicit_rejection",
            }
            samples.append(sample)

        return samples

    def generate_full_dataset(
        self,
        normal_count: int = 350,
        anomaly_count: int = 150
    ) -> pd.DataFrame:
        """Generate complete dataset with normal and anomalous samples."""
        _LOGGER.info("Generating full dataset...")
        
        all_samples = []

        # Generate normal samples across all suites
        for suite in ["ML-KEM-768", "ML-KEM-1024", "Classical"]:
            count = normal_count // 3
            all_samples.extend(self.generate_normal_handshake(suite, count))

        # Generate anomalous samples
        # Timing anomalies (moderate severity)
        for suite in ["ML-KEM-768", "ML-KEM-1024"]:
            all_samples.extend(self.generate_timing_anomaly(suite, 20, "moderate"))

        # Size anomalies
        for suite in ["ML-KEM-768", "ML-KEM-1024"]:
            all_samples.extend(self.generate_size_anomaly(suite, 15, "ciphertext_tampering"))
            all_samples.extend(self.generate_size_anomaly(suite, 15, "public_key_tampering"))

        # Implicit rejections
        for suite in ["ML-KEM-768", "ML-KEM-1024"]:
            all_samples.extend(self.generate_implicit_rejection(suite, 15))

        # Convert to DataFrame
        df = pd.DataFrame(all_samples)
        
        # Shuffle dataset
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        self.dataset = df
        return df

    def export_dataset(
        self,
        filename: str = "handshake_dataset.csv"
    ) -> Path:
        """Export dataset to CSV format."""
        if self.dataset is None or self.dataset.empty:
            _LOGGER.error("No dataset to export")
            return None

        output_path = self.output_dir / filename
        self.dataset.to_csv(output_path, index=False)
        _LOGGER.info(f"Dataset exported to {output_path}")
        return output_path

    def export_statistics(self, filename: str = "dataset_statistics.json") -> Path:
        """Export dataset statistics."""
        if self.dataset is None or self.dataset.empty:
            _LOGGER.error("No dataset to analyze")
            return None

        stats = {
            "total_samples": len(self.dataset),
            "normal_samples": int((self.dataset["label"] == 0).sum()),
            "anomalous_samples": int((self.dataset["label"] == 1).sum()),
            "class_balance": {
                "normal": float((self.dataset["label"] == 0).sum() / len(self.dataset)),
                "anomalous": float((self.dataset["label"] == 1).sum() / len(self.dataset)),
            },
            "by_suite": {},
            "by_anomaly_type": {},
        }

        # Statistics by suite
        for suite in self.dataset["suite"].unique():
            suite_data = self.dataset[self.dataset["suite"] == suite]
            stats["by_suite"][suite] = {
                "count": len(suite_data),
                "normal": int((suite_data["label"] == 0).sum()),
                "anomalous": int((suite_data["label"] == 1).sum()),
                "mean_latency_ms": float(suite_data["latency_ms"].mean()),
                "std_latency_ms": float(suite_data["latency_ms"].std()),
            }

        # Statistics by anomaly type
        for anomaly_type in self.dataset["anomaly_type"].unique():
            anomaly_data = self.dataset[self.dataset["anomaly_type"] == anomaly_type]
            stats["by_anomaly_type"][anomaly_type] = {
                "count": len(anomaly_data),
                "mean_latency_ms": float(anomaly_data["latency_ms"].mean()),
            }

        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(stats, f, indent=2)
        _LOGGER.info(f"Statistics exported to {output_path}")
        return output_path

    def print_summary(self):
        """Print dataset summary."""
        if self.dataset is None or self.dataset.empty:
            _LOGGER.error("No dataset to summarize")
            return

        _LOGGER.info("\n=== Dataset Summary ===")
        _LOGGER.info(f"Total samples: {len(self.dataset)}")
        _LOGGER.info(f"Normal: {(self.dataset['label'] == 0).sum()} ({(self.dataset['label'] == 0).sum() / len(self.dataset) * 100:.1f}%)")
        _LOGGER.info(f"Anomalous: {(self.dataset['label'] == 1).sum()} ({(self.dataset['label'] == 1).sum() / len(self.dataset) * 100:.1f}%)")
        _LOGGER.info("\nBy Suite:")
        for suite in self.dataset["suite"].unique():
            suite_data = self.dataset[self.dataset["suite"] == suite]
            _LOGGER.info(f"  {suite}: {len(suite_data)} samples")
        _LOGGER.info("\nBy Anomaly Type:")
        for anomaly_type in self.dataset["anomaly_type"].unique():
            count = (self.dataset["anomaly_type"] == anomaly_type).sum()
            _LOGGER.info(f"  {anomaly_type}: {count} samples")


def main():
    """Main dataset generation pipeline."""
    _LOGGER.info("=== 3SA Dataset Generation ===")
    _LOGGER.info("Using literature-based parameters for rigorous PQC validation")
    
    generator = DatasetGenerator()
    
    # Generate full dataset
    df = generator.generate_full_dataset(normal_count=350, anomaly_count=150)
    
    # Export dataset
    generator.export_dataset("handshake_dataset.csv")
    
    # Export statistics
    generator.export_statistics("dataset_statistics.json")
    
    # Print summary
    generator.print_summary()
    
    _LOGGER.info("\n=== Dataset Generation Complete ===")
    _LOGGER.info("Files saved to datasets/ directory")
    _LOGGER.info("Use handshake_dataset.csv for training ai_anomaly_detector.py")


if __name__ == "__main__":
    main()
