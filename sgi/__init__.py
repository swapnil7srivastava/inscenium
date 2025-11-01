"""Inscenium Scene Graph Intelligence (SGI) Module"""

from .sgi_builder import build_sgi
from .sgi_matcher import match_surfaces
from .rights_ledger import RightsEntry, manage_rights

__version__ = "1.0.0"
__all__ = ["build_sgi", "match_surfaces", "RightsEntry", "manage_rights"]