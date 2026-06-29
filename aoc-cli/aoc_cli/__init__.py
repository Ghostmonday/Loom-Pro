"""Loom CLI — gravity engine and analysis commands."""

from .cli import app
from .gravity import CURVATURE_HARD_FLOOR, GRAVITY_HARD_FLOOR, compute_gravity_and_curvature
from .inferring import infer_reflective_layer

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CURVATURE_HARD_FLOOR",
    "GRAVITY_HARD_FLOOR",
    "compute_gravity_and_curvature",
    "infer_reflective_layer",
    "app",
]
