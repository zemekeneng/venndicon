"""Venndicon - Generate random Venn diagram SVG icons."""

from .core import (
    Venndicon,
    VenndiconGrid,
    QuadrantColors,
    ImageGridAnalysis,
    MatchedGrid,
    generate,
    generate_svg,
    grid,
    analyze_quadrants,
    analyze_image_grid,
    match_venndicons_to_image,
)

__version__ = "0.1.0"
__all__ = [
    "Venndicon",
    "VenndiconGrid",
    "QuadrantColors",
    "ImageGridAnalysis",
    "MatchedGrid",
    "generate",
    "generate_svg",
    "grid",
    "analyze_quadrants",
    "analyze_image_grid",
    "match_venndicons_to_image",
]

