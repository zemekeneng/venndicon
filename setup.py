from setuptools import setup, find_packages

setup(
    name="venndicon",
    version="0.1.0",
    description="Generate random Venn diagram SVG icons",
    author="BCR",
    packages=find_packages(),
    install_requires=[
        "svgwrite>=1.4.0",
    ],
    extras_require={
        "notebook": ["jupyter", "ipython"],
        "raster": ["cairosvg>=2.5.0", "Pillow>=8.0.0"],
        "all": ["jupyter", "ipython", "cairosvg>=2.5.0", "Pillow>=8.0.0"],
    },
    python_requires=">=3.7",
)

