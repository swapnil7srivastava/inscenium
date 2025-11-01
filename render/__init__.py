"""Inscenium Render Module - CUDA compositing and quality control."""

from .compositor_bindings import composite_frame
from .qc_metrics import calculate_prs_score, check_quality_thresholds
from .sidecar_packager import package_sidecar

__all__ = ["composite_frame", "calculate_prs_score", "check_quality_thresholds", "package_sidecar"]