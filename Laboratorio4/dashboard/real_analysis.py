"""Inferência dos dados reais, separada da demonstração simulada da S01."""

from pathlib import Path

from src.collect import ROOT
from src.data import load_real
from src.statistics import test_proportion


def analyze_real(path: Path = ROOT / "data" / "real_ci.csv", *, p0=0.05, alpha=0.05):
    rows, _ = load_real(path)
    sample = [int(row["failed"]) for row in rows]
    return test_proportion(sample, p0=p0, alpha=alpha)
