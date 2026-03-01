# Venndicon

A Venn diagram icon -- three overlapping circles with random positions, sizes, and colors for each of the eight regions.

**[Live demo & explanation](https://zemekeneng.github.io/venndicon/)**

## How Venndicons Are Produced

Each venndicon is a small SVG built from three circles drawn on a square canvas. The circles overlap to create a classic Venn diagram with eight distinct regions, and every region gets its own randomly chosen color.

Each circle has a random **center position** (20-80% of the canvas on each axis) and a random **radius** (40-100% of the canvas width). That's 9 geometric values plus 8 colors = **17 random values** per venndicon.

The eight regions are:

| # | Region | Description |
|---|--------|-------------|
| 1 | Background | Area outside all circles |
| 2 | A only | Inside circle A, outside B and C |
| 3 | B only | Inside circle B, outside A and C |
| 4 | C only | Inside circle C, outside A and B |
| 5 | A ∩ B | Intersection of A and B only |
| 6 | A ∩ C | Intersection of A and C only |
| 7 | B ∩ C | Intersection of B and C only |
| 8 | A ∩ B ∩ C | Triple intersection |

When a seed integer is provided, the random number generator is deterministic -- the same seed always produces the same venndicon.

## Installation

```bash
pip install -e .
```

For image matching (requires raster support):

```bash
pip install -e ".[all]"
```

## Usage

### Python API

```python
from venndicon import generate, grid

# Single venndicon
icon = generate(seed=42)
icon.save("my_icon.svg")

# Grid of venndicons
g = grid(rows=4, cols=6, cell_size=100, start_seed=0)
g.save("my_grid.svg")
```

### CLI -- Matching Venndicons to Images

```bash
venndicon photo.jpg --cols 80 --rows 80 --format jpeg > manifest.json
```

This generates a grid of venndicons arranged to approximate the input photograph. The process:

1. **Divide** the target image into a grid of cells (e.g. 80x80)
2. **Analyze** each cell's average color in four quadrants (TL, TR, BL, BR)
3. **Generate** a pool of candidate venndicons, analyzing their quadrant colors the same way
4. **Solve** the optimal one-to-one assignment using the Hungarian algorithm

Multiple images can share a venndicon pool:

```bash
venndicon dad.jpg mom.jpg --cols 80 --rows 80 > manifest.json
```

## The Hungarian Algorithm

The assignment problem is: given *n* venndicons and *m* image cells with a color distance for every pair, find a one-to-one assignment that minimizes total cost.

The color distance between a venndicon and an image cell is the sum of squared Euclidean RGB distances across all four quadrants:

```
distance = sum(
    (r_v - r_i)^2 + (g_v - g_i)^2 + (b_v - b_i)^2
    for each quadrant in [TL, TR, BL, BR]
)
```

The algorithm (published by Harold Kuhn in 1955, refined by Munkres in 1957) works by maintaining dual variables (potentials) for rows and columns and iteratively extending a maximum matching among "tight" edges:

1. **Initialize potentials** -- set each row potential to the minimum cost in that row
2. **Find tight edges and build a matching** -- an edge (i,j) is tight when `C[i][j] - u[i] - v[j] = 0`
3. **Check for optimality** -- if every row is matched, stop; otherwise adjust potentials to create new tight edges
4. **Repeat** until a perfect matching is found

The algorithm runs in **O(n^3)** time. The implementation uses `scipy.optimize.linear_sum_assignment` (Jonker-Volgenant / LAPJV), which finishes in seconds even for an 80x80 grid (6,400 cells).

A greedy approach would be faster but suboptimal -- early assignments can steal good venndicons from cells that have no other good match. The Hungarian algorithm guarantees the **global optimum**.

## CLI Options

```
venndicon [images...] [options]

  --cols N          Grid columns (default: 50)
  --rows N          Grid rows (default: 50)
  --cell-size N     Pixel size per cell (default: 10)
  --start-seed N    Starting seed (default: 0)
  --format FORMAT   Output format: svg, jpeg, png (default: svg)
  --scale F         Scale factor for raster output (default: 1.0)
  --quality N       JPEG quality 1-100 (default: 90)
  --gap N           Gap between cells in pixels (default: 0)
  --prefix STR      Output filename prefix (default: matched_)
  --output-dir DIR  Output directory (default: .)
  --no-image-colors Disable palette sampling from the image
  --background HEX  Grid background color (default: #222222)
```

## License

MIT -- see [LICENCE](LICENCE).
