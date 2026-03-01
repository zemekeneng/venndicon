"""Core Venndicon SVG generation logic."""

import io
import math
import random
import uuid
from typing import Optional, Union, List
import svgwrite

# Optional dependencies for raster export
try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _check_raster_deps():
    """Check if raster export dependencies are available."""
    if not HAS_CAIROSVG:
        raise ImportError(
            "cairosvg is required for PNG/JPEG export. "
            "Install it with: pip install cairosvg"
        )


def _svg_to_png_bytes(svg_string: str, scale: float = 1.0) -> bytes:
    """Convert SVG string to PNG bytes."""
    _check_raster_deps()
    return cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)


def _svg_to_jpeg_bytes(svg_string: str, scale: float = 1.0, quality: int = 90) -> bytes:
    """Convert SVG string to JPEG bytes."""
    _check_raster_deps()
    if not HAS_PIL:
        raise ImportError(
            "Pillow is required for JPEG export. "
            "Install it with: pip install Pillow"
        )
    
    # Convert SVG to PNG first
    png_bytes = cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), scale=scale)
    
    # Convert PNG to JPEG using Pillow
    png_image = Image.open(io.BytesIO(png_bytes))
    
    # Convert RGBA to RGB (JPEG doesn't support transparency)
    if png_image.mode == 'RGBA':
        # Create white background
        background = Image.new('RGB', png_image.size, (255, 255, 255))
        background.paste(png_image, mask=png_image.split()[3])
        png_image = background
    elif png_image.mode != 'RGB':
        png_image = png_image.convert('RGB')
    
    # Save to bytes
    jpeg_buffer = io.BytesIO()
    png_image.save(jpeg_buffer, format='JPEG', quality=quality)
    return jpeg_buffer.getvalue()


def _load_image(source) -> "Image.Image":
    """Load an image from various sources.
    
    Args:
        source: Can be a file path (str), PIL Image, Venndicon, or VenndiconGrid.
    
    Returns:
        PIL Image object.
    """
    if not HAS_PIL:
        raise ImportError(
            "Pillow is required for image analysis. "
            "Install it with: pip install Pillow"
        )
    
    # If it's already a PIL Image
    if isinstance(source, Image.Image):
        return source
    
    # If it's a Venndicon or VenndiconGrid (has to_svg method)
    if hasattr(source, 'to_svg'):
        _check_raster_deps()
        png_bytes = cairosvg.svg2png(bytestring=source.to_svg().encode('utf-8'))
        return Image.open(io.BytesIO(png_bytes))
    
    # If it's a file path
    if isinstance(source, str):
        if source.lower().endswith('.svg'):
            _check_raster_deps()
            with open(source, 'r') as f:
                svg_content = f.read()
            png_bytes = cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
            return Image.open(io.BytesIO(png_bytes))
        else:
            return Image.open(source)
    
    raise ValueError(f"Cannot load image from {type(source)}")


class QuadrantColors:
    """Container for quadrant color analysis results."""
    
    def __init__(self, top_left, top_right, bottom_left, bottom_right):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
    
    def __repr__(self):
        return (
            f"QuadrantColors(\n"
            f"  top_left={self.top_left},\n"
            f"  top_right={self.top_right},\n"
            f"  bottom_left={self.bottom_left},\n"
            f"  bottom_right={self.bottom_right}\n"
            f")"
        )
    
    def to_dict(self):
        """Return as dictionary."""
        return {
            'top_left': self.top_left,
            'top_right': self.top_right,
            'bottom_left': self.bottom_left,
            'bottom_right': self.bottom_right,
        }
    
    def to_hex(self):
        """Return colors as hex strings."""
        def rgb_to_hex(rgb):
            return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        return {
            'top_left': rgb_to_hex(self.top_left),
            'top_right': rgb_to_hex(self.top_right),
            'bottom_left': rgb_to_hex(self.bottom_left),
            'bottom_right': rgb_to_hex(self.bottom_right),
        }


def analyze_quadrants(source) -> QuadrantColors:
    """Analyze a square image and calculate average RGB for each quadrant.
    
    Divides the image into 4 quadrants:
    - top_left: upper-left quarter
    - top_right: upper-right quarter
    - bottom_left: lower-left quarter
    - bottom_right: lower-right quarter
    
    Args:
        source: Image source - can be:
            - File path (str) to JPEG, PNG, or SVG
            - PIL Image object
            - Venndicon instance
            - VenndiconGrid instance
    
    Returns:
        QuadrantColors object with average RGB tuples for each quadrant.
    
    Example:
        >>> from venndicon import generate, analyze_quadrants
        >>> icon = generate(seed=42)
        >>> colors = analyze_quadrants(icon)
        >>> print(colors.top_left)  # (r, g, b)
        >>> print(colors.to_hex())  # {'top_left': '#abc123', ...}
    """
    import numpy as np
    
    # Load the image
    img = _load_image(source)
    
    # Convert to RGB if necessary
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get dimensions
    width, height = img.size
    
    # Calculate midpoints
    mid_x = width // 2
    mid_y = height // 2
    
    # Convert to numpy array for efficient calculation
    pixels = np.array(img)
    
    # Extract quadrants
    top_left = pixels[0:mid_y, 0:mid_x]
    top_right = pixels[0:mid_y, mid_x:width]
    bottom_left = pixels[mid_y:height, 0:mid_x]
    bottom_right = pixels[mid_y:height, mid_x:width]
    
    # Calculate average RGB for each quadrant
    def avg_rgb(quadrant):
        avg = quadrant.mean(axis=(0, 1))
        return (int(round(avg[0])), int(round(avg[1])), int(round(avg[2])))
    
    return QuadrantColors(
        top_left=avg_rgb(top_left),
        top_right=avg_rgb(top_right),
        bottom_left=avg_rgb(bottom_left),
        bottom_right=avg_rgb(bottom_right),
    )


class ImageGridAnalysis:
    """Container for image grid analysis results."""
    
    def __init__(self, cols: int, rows: int, cell_size: int, cells: list):
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.cells = cells  # 2D list of QuadrantColors [row][col]
    
    def __repr__(self):
        return f"ImageGridAnalysis(cols={self.cols}, rows={self.rows}, cell_size={self.cell_size}px, total_cells={self.cols * self.rows})"
    
    def get(self, col: int, row: int) -> QuadrantColors:
        """Get QuadrantColors for a specific cell."""
        return self.cells[row][col]
    
    def to_dict(self):
        """Return all cells as nested dictionaries."""
        result = []
        for row in range(self.rows):
            row_data = []
            for col in range(self.cols):
                row_data.append({
                    'col': col,
                    'row': row,
                    'quadrants': self.cells[row][col].to_hex()
                })
            result.append(row_data)
        return result
    
    def flat(self):
        """Return all cells as a flat list with coordinates."""
        result = []
        for row in range(self.rows):
            for col in range(self.cols):
                result.append({
                    'col': col,
                    'row': row,
                    'quadrants': self.cells[row][col]
                })
        return result


def analyze_image_grid(source, cols: int, rows: int) -> ImageGridAnalysis:
    """Analyze an image by dividing it into a grid of squares.
    
    The image is cropped to fit the grid dimensions exactly, centered on
    the original image. Each cell is then analyzed for quadrant colors.
    
    Args:
        source: Image source - file path (str) or PIL Image.
        cols: Number of columns (squares across).
        rows: Number of rows (squares down).
    
    Returns:
        ImageGridAnalysis object containing QuadrantColors for each cell.
    
    Example:
        >>> from venndicon import analyze_image_grid
        >>> result = analyze_image_grid("photo.jpg", cols=10, rows=12)
        >>> print(result)  # ImageGridAnalysis(cols=10, rows=12, ...)
        >>> cell = result.get(5, 3)  # Get cell at column 5, row 3
        >>> print(cell.to_hex())  # Quadrant colors for that cell
    """
    import numpy as np
    
    if not HAS_PIL:
        raise ImportError(
            "Pillow is required for image analysis. "
            "Install it with: pip install Pillow"
        )
    
    # Load the image
    if isinstance(source, str):
        img = Image.open(source)
    elif isinstance(source, Image.Image):
        img = source
    else:
        raise ValueError(f"source must be a file path or PIL Image, got {type(source)}")
    
    # Convert to RGB if necessary
    if img.mode == 'RGBA':
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    
    # Calculate the largest square size that fits the grid
    cell_size_from_width = width // cols
    cell_size_from_height = height // rows
    cell_size = min(cell_size_from_width, cell_size_from_height)
    
    if cell_size < 1:
        raise ValueError(f"Image too small for {cols}x{rows} grid. Image is {width}x{height}.")
    
    # Calculate total grid size
    grid_width = cell_size * cols
    grid_height = cell_size * rows
    
    # Calculate crop offsets to center the grid
    offset_x = (width - grid_width) // 2
    offset_y = (height - grid_height) // 2
    
    # Crop the image to the grid area
    img_cropped = img.crop((offset_x, offset_y, offset_x + grid_width, offset_y + grid_height))
    pixels = np.array(img_cropped)
    
    # Analyze each cell
    cells = []
    for row in range(rows):
        row_cells = []
        for col in range(cols):
            # Extract the cell
            x1 = col * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            cell_pixels = pixels[y1:y2, x1:x2]
            
            # Calculate quadrant boundaries within the cell
            mid_x = cell_size // 2
            mid_y = cell_size // 2
            
            top_left = cell_pixels[0:mid_y, 0:mid_x]
            top_right = cell_pixels[0:mid_y, mid_x:cell_size]
            bottom_left = cell_pixels[mid_y:cell_size, 0:mid_x]
            bottom_right = cell_pixels[mid_y:cell_size, mid_x:cell_size]
            
            def avg_rgb(quadrant):
                if quadrant.size == 0:
                    return (0, 0, 0)
                avg = quadrant.mean(axis=(0, 1))
                return (int(round(avg[0])), int(round(avg[1])), int(round(avg[2])))
            
            quadrant_colors = QuadrantColors(
                top_left=avg_rgb(top_left),
                top_right=avg_rgb(top_right),
                bottom_left=avg_rgb(bottom_left),
                bottom_right=avg_rgb(bottom_right),
            )
            row_cells.append(quadrant_colors)
        cells.append(row_cells)
    
    return ImageGridAnalysis(cols=cols, rows=rows, cell_size=cell_size, cells=cells)


def _quadrant_color_distance(q1: QuadrantColors, q2: QuadrantColors) -> float:
    """Calculate squared color distance between two QuadrantColors.
    
    Returns sum of squared RGB differences for all 4 quadrants.
    """
    def rgb_dist_sq(c1, c2):
        return (c1[0] - c2[0])**2 + (c1[1] - c2[1])**2 + (c1[2] - c2[2])**2
    
    return (
        rgb_dist_sq(q1.top_left, q2.top_left) +
        rgb_dist_sq(q1.top_right, q2.top_right) +
        rgb_dist_sq(q1.bottom_left, q2.bottom_left) +
        rgb_dist_sq(q1.bottom_right, q2.bottom_right)
    )


class MatchedGrid:
    """Result of matching Venndicons to an image grid.
    
    Contains both the original (seed order) and matched (optimized) arrangements
    of the exact same set of Venndicons.
    """
    
    def __init__(
        self, 
        cols: int, 
        rows: int, 
        cell_size: int,
        venndicons: list,
        assignment: list,
        total_distance: float,
        image_analysis: ImageGridAnalysis,
        original_venndicons: list = None,
        start_seed: int = None,
    ):
        self.cols = cols
        self.rows = rows
        self.cell_size = cell_size
        self.venndicons = venndicons  # 2D list [row][col] of Venndicon objects (matched order)
        self.assignment = assignment  # List of (venndicon_index, image_cell_index) pairs
        self.total_distance = total_distance
        self.image_analysis = image_analysis
        self._original_venndicons = original_venndicons  # Flat list in original seed order
        self.start_seed = start_seed
    
    def __repr__(self):
        return (
            f"MatchedGrid(cols={self.cols}, rows={self.rows}, "
            f"total_distance={self.total_distance:.0f})"
        )
    
    def get(self, col: int, row: int) -> "Venndicon":
        """Get the Venndicon at a specific grid position in the matched arrangement."""
        return self.venndicons[row][col]
    
    def original_grid(self, gap: int = 5, background: str = "#222222") -> "VenndiconGrid":
        """Create a VenndiconGrid with the original seed order.
        
        Args:
            gap: Gap between cells in pixels.
            background: Background color for the grid.
        
        Returns:
            VenndiconGrid with icons in original seed order.
        """
        grid_obj = VenndiconGrid.__new__(VenndiconGrid)
        grid_obj.rows = self.rows
        grid_obj.cols = self.cols
        grid_obj.cell_size = self.cell_size
        grid_obj.gap = gap
        grid_obj.background = background
        grid_obj.start_seed = self.start_seed
        grid_obj._uid = uuid.uuid4().hex[:8]
        grid_obj.icons = list(self._original_venndicons)  # Copy original order
        return grid_obj
    
    def to_grid(self, gap: int = 5, background: str = "#222222") -> "VenndiconGrid":
        """Create a VenndiconGrid from the matched (optimized) arrangement.
        
        Args:
            gap: Gap between cells in pixels.
            background: Background color for the grid.
        
        Returns:
            VenndiconGrid with icons arranged optimally to match the image.
        """
        grid_obj = VenndiconGrid.__new__(VenndiconGrid)
        grid_obj.rows = self.rows
        grid_obj.cols = self.cols
        grid_obj.cell_size = self.cell_size
        grid_obj.gap = gap
        grid_obj.background = background
        grid_obj.start_seed = None
        grid_obj._uid = uuid.uuid4().hex[:8]
        
        # Flatten the 2D venndicons list (matched order)
        grid_obj.icons = []
        for row in range(self.rows):
            for col in range(self.cols):
                grid_obj.icons.append(self.venndicons[row][col])
        
        return grid_obj
    
    def save_comparison(self, filename: str, gap: int = 5):
        """Save the matched grid to a file."""
        grid_obj = self.to_grid(gap=gap)
        grid_obj.save(filename)


def _extract_color_palette(image_analysis: ImageGridAnalysis) -> list:
    """Extract all colors from image analysis as a palette.
    
    Returns a list of RGB tuples from all quadrants of all cells.
    """
    palette = []
    for row in range(image_analysis.rows):
        for col in range(image_analysis.cols):
            q = image_analysis.get(col, row)
            palette.append(q.top_left)
            palette.append(q.top_right)
            palette.append(q.bottom_left)
            palette.append(q.bottom_right)
    return palette


def _sample_color_from_palette(palette: list, rng) -> str:
    """Sample a color from the palette and return as hex string."""
    rgb = rng.choice(palette)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def match_venndicons_to_image(
    image_sources,
    cols: int,
    rows: int,
    start_seed: int = 0,
    cell_size: int = 100,
    use_image_colors: bool = True,
) -> Union[MatchedGrid, List[MatchedGrid]]:
    """Match Venndicons to one or more images by minimizing color distance.
    
    Generates a shared pool of Venndicons with sequential seeds, then uses the
    Hungarian algorithm to find the optimal arrangement for each image that
    minimizes total squared color distance between Venndicon quadrants and
    image cell quadrants.
    
    When multiple images are provided:
    - The combined color distribution of all images is used when
      use_image_colors=True.
    - A single shared pool of Venndicons is created (sized for the largest grid).
    - Each image gets its own optimal arrangement from that pool.
    - If images have different dimensions, grid sizes are computed per-image
      to preserve aspect ratio without distortion, using at most cols×rows
      total cells. Excess Venndicons are discarded to maintain perfect
      rectangles.
    
    Args:
        image_sources: Image(s) to match - a single source (file path or PIL
                       Image) or a list of sources.
        cols: Number of columns for the first image's grid (other images
              derive their grid from the first image's cell count and their
              own aspect ratio).
        rows: Number of rows for the first image's grid.
        start_seed: Starting seed for generating Venndicons.
        cell_size: Size of each Venndicon in the output grid.
        use_image_colors: If True, Venndicon colors are sampled from the
                         combined color palette of all images.
    
    Returns:
        A single MatchedGrid if one image is provided, or a list of
        MatchedGrid objects (one per image) if multiple images are provided.
    
    Example:
        >>> from venndicon import match_venndicons_to_image
        >>> result = match_venndicons_to_image("photo.jpg", cols=5, rows=5)
        >>> matched = result.to_grid()
        >>>
        >>> results = match_venndicons_to_image(
        ...     ["mom.jpg", "dad.jpg"], cols=10, rows=12
        ... )
        >>> for r in results:
        ...     r.to_grid().save_jpeg("out.jpg")
    """
    import numpy as np

    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError:
        raise ImportError(
            "scipy is required for Venndicon matching. "
            "Install it with: pip install scipy"
        )

    single_image = not isinstance(image_sources, (list, tuple))
    if single_image:
        image_sources = [image_sources]

    if not image_sources:
        raise ValueError("At least one image source is required")

    # Load all images to get their dimensions
    pil_images = [_load_image(src) for src in image_sources]

    primary_cells = cols * rows

    grid_specs = []  # (cols, rows) per image
    for i, img in enumerate(pil_images):
        if i == 0:
            grid_specs.append((cols, rows))
        else:
            w, h = img.size
            aspect = w / h
            # Solve for img_rows such that
            # (aspect * img_rows) * img_rows <= primary_cells
            img_rows = max(1, int(math.sqrt(primary_cells / aspect)))
            img_cols = max(1, int(aspect * img_rows))
            # Trim if we slightly overshot due to rounding
            while img_cols * img_rows > primary_cells:
                if img_cols >= img_rows:
                    img_cols -= 1
                else:
                    img_rows -= 1
            grid_specs.append((img_cols, img_rows))

    max_cells = max(c * r for c, r in grid_specs)

    # Analyze every image at its own grid dimensions
    image_analyses = []
    for img, (g_cols, g_rows) in zip(pil_images, grid_specs):
        image_analyses.append(analyze_image_grid(img, cols=g_cols, rows=g_rows))

    # Build a combined color palette from ALL images
    palette = None
    if use_image_colors:
        palette = []
        for analysis in image_analyses:
            palette.extend(_extract_color_palette(analysis))

    # Generate the shared pool of Venndicons (enough for the largest grid)
    venndicons = []
    venndicon_quad_colors = []
    for i in range(max_cells):
        seed = start_seed + i
        if use_image_colors and palette:
            rng = np.random.default_rng(seed)
            v_colors = [_sample_color_from_palette(palette, rng) for _ in range(8)]
            v = Venndicon(size=cell_size, seed=seed, colors=v_colors)
        else:
            v = Venndicon(size=cell_size, seed=seed)
        venndicons.append(v)
        venndicon_quad_colors.append(analyze_quadrants(v))

    # Match venndicons to each image independently
    results = []
    for analysis, (g_cols, g_rows) in zip(image_analyses, grid_specs):
        num_cells = g_cols * g_rows

        # Flatten image cell colours
        image_cell_colors = []
        for row in range(g_rows):
            for col in range(g_cols):
                image_cell_colors.append(analysis.get(col, row))

        # Cost matrix: (max_cells × num_cells).  When the pool is larger than
        # the grid, linear_sum_assignment selects the best subset.
        cost_matrix = np.zeros((max_cells, num_cells))
        for vi, vc in enumerate(venndicon_quad_colors):
            for ci, ic in enumerate(image_cell_colors):
                cost_matrix[vi, ci] = _quadrant_color_distance(vc, ic)

        v_indices, c_indices = linear_sum_assignment(cost_matrix)

        cell_to_venndicon = {}
        for v_idx, c_idx in zip(v_indices, c_indices):
            cell_to_venndicon[c_idx] = v_idx

        venndicons_2d = []
        total_distance = 0
        assignment = []
        for row in range(g_rows):
            row_venndicons = []
            for col in range(g_cols):
                cell_idx = row * g_cols + col
                venndicon_idx = cell_to_venndicon[cell_idx]
                row_venndicons.append(venndicons[venndicon_idx])
                assignment.append((venndicon_idx, cell_idx))
                total_distance += cost_matrix[venndicon_idx, cell_idx]
            venndicons_2d.append(row_venndicons)

        # Store the assigned subset in seed order for original_grid()
        used_indices = sorted(cell_to_venndicon.values())
        original_subset = [venndicons[idx] for idx in used_indices]

        results.append(MatchedGrid(
            cols=g_cols,
            rows=g_rows,
            cell_size=cell_size,
            venndicons=venndicons_2d,
            assignment=assignment,
            total_distance=total_distance,
            image_analysis=analysis,
            original_venndicons=original_subset,
            start_seed=start_seed,
        ))

    if single_image:
        return results[0]
    return results


def random_color() -> str:
    """Generate a random hex color."""
    r = random.randint(1, 255)
    g = random.randint(1, 255)
    b = random.randint(1, 255)
    return f"#{r:02x}{g:02x}{b:02x}"


class Venndicon:
    """A Venn diagram icon generator.
    
    Creates an SVG with three overlapping circles with random positions,
    sizes, and colors for each region (including intersections).
    """
    
    def __init__(
        self,
        size: int = 500,
        seed: Optional[int] = None,
        colors: Optional[list] = None,
    ):
        """Initialize a Venndicon.
        
        Args:
            size: The width and height of the SVG in pixels.
            seed: Optional random seed for reproducible results.
            colors: Optional list of 8 colors for the regions.
        """
        self.size = size
        self.seed = seed
        # Generate unique ID for this instance (used for clip path IDs to avoid conflicts)
        self._uid = uuid.uuid4().hex[:8]
        
        if seed is not None:
            random.seed(seed)
        
        # Generate circle positions (20%-80% of canvas)
        self.cx1 = random.randint(2, 8) * size // 10
        self.cx2 = random.randint(2, 8) * size // 10
        self.cx3 = random.randint(2, 8) * size // 10
        self.cy1 = random.randint(2, 8) * size // 10
        self.cy2 = random.randint(2, 8) * size // 10
        self.cy3 = random.randint(2, 8) * size // 10
        
        # Generate circle radii (40%-100% of canvas)
        self.cr1 = random.randint(4, 10) * size // 10
        self.cr2 = random.randint(4, 10) * size // 10
        self.cr3 = random.randint(4, 10) * size // 10
        
        # Generate colors if not provided
        if colors is not None:
            if len(colors) != 8:
                raise ValueError("colors must be a list of 8 color strings")
            self.colors = colors
        else:
            self.colors = [random_color() for _ in range(8)]
    
    @property
    def background_color(self) -> str:
        """Background rectangle color."""
        return self.colors[0]
    
    @property
    def circle1_color(self) -> str:
        """Circle 1 only color."""
        return self.colors[1]
    
    @property
    def circle2_color(self) -> str:
        """Circle 2 only color."""
        return self.colors[2]
    
    @property
    def circle3_color(self) -> str:
        """Circle 3 only color."""
        return self.colors[3]
    
    @property
    def intersection12_color(self) -> str:
        """Circle 1 & 2 intersection color."""
        return self.colors[4]
    
    @property
    def intersection13_color(self) -> str:
        """Circle 1 & 3 intersection color."""
        return self.colors[5]
    
    @property
    def intersection23_color(self) -> str:
        """Circle 2 & 3 intersection color."""
        return self.colors[6]
    
    @property
    def intersection123_color(self) -> str:
        """All three circles intersection color."""
        return self.colors[7]
    
    def to_svg(self) -> str:
        """Generate the SVG as a string.
        
        Returns:
            The SVG markup as a string.
        """
        dwg = svgwrite.Drawing(size=(self.size, self.size))
        uid = self._uid  # Unique prefix for clip path IDs
        
        # Define clip paths for intersections
        defs = dwg.defs
        
        # Clip path for circle 2 (used for 1∩2)
        clip2 = dwg.clipPath(id=f"clip2_{uid}")
        clip2.add(dwg.circle(center=(self.cx2, self.cy2), r=self.cr2 / 2))
        defs.add(clip2)
        
        # Clip path for circle 3 (used for 1∩3)
        clip3 = dwg.clipPath(id=f"clip3_{uid}")
        clip3.add(dwg.circle(center=(self.cx3, self.cy3), r=self.cr3 / 2))
        defs.add(clip3)
        
        # Clip path for circle 3 (used for 2∩3)
        clip3a = dwg.clipPath(id=f"clip3a_{uid}")
        clip3a.add(dwg.circle(center=(self.cx3, self.cy3), r=self.cr3 / 2))
        defs.add(clip3a)
        
        # Clip path for circle 1 (used for triple intersection)
        clip1 = dwg.clipPath(id=f"clip1_{uid}")
        clip1.add(dwg.circle(center=(self.cx1, self.cy1), r=self.cr1 / 2))
        defs.add(clip1)
        
        # Combined clip for triple intersection: circle 3 clipped by circle 1
        # The clipPath itself can have a clip-path attribute
        clip_triple = dwg.clipPath(id=f"clip_triple_{uid}")
        clip_triple['clip-path'] = f"url(#clip1_{uid})"
        clip_triple.add(dwg.circle(center=(self.cx3, self.cy3), r=self.cr3 / 2))
        defs.add(clip_triple)
        
        # Background rectangle
        dwg.add(dwg.rect(insert=(0, 0), size=(self.size, self.size), fill=self.background_color))
        
        # Circle 1
        dwg.add(dwg.circle(
            center=(self.cx1, self.cy1),
            r=self.cr1 / 2,
            fill=self.circle1_color
        ))
        
        # Circle 2
        dwg.add(dwg.circle(
            center=(self.cx2, self.cy2),
            r=self.cr2 / 2,
            fill=self.circle2_color
        ))
        
        # Circle 3
        dwg.add(dwg.circle(
            center=(self.cx3, self.cy3),
            r=self.cr3 / 2,
            fill=self.circle3_color
        ))
        
        # Intersection 1∩2: circle 1 clipped by circle 2
        ci12 = dwg.circle(
            center=(self.cx1, self.cy1),
            r=self.cr1 / 2,
            fill=self.intersection12_color
        )
        ci12['clip-path'] = f"url(#clip2_{uid})"
        dwg.add(ci12)
        
        # Intersection 1∩3: circle 1 clipped by circle 3
        ci13 = dwg.circle(
            center=(self.cx1, self.cy1),
            r=self.cr1 / 2,
            fill=self.intersection13_color
        )
        ci13['clip-path'] = f"url(#clip3_{uid})"
        dwg.add(ci13)
        
        # Intersection 2∩3: circle 2 clipped by circle 3
        ci23 = dwg.circle(
            center=(self.cx2, self.cy2),
            r=self.cr2 / 2,
            fill=self.intersection23_color
        )
        ci23['clip-path'] = f"url(#clip3a_{uid})"
        dwg.add(ci23)
        
        # Triple intersection 1∩2∩3: circle 2 clipped by (circle 3 and circle 1)
        c123 = dwg.circle(
            center=(self.cx2, self.cy2),
            r=self.cr2 / 2,
            fill=self.intersection123_color
        )
        c123['clip-path'] = f"url(#clip_triple_{uid})"
        dwg.add(c123)
        
        return dwg.tostring()
    
    def save(self, filename: str) -> None:
        """Save the SVG to a file.
        
        Args:
            filename: The output filename (should end in .svg).
        """
        svg_content = self.to_svg()
        with open(filename, 'w') as f:
            f.write(svg_content)
    
    def save_png(self, filename: str, scale: float = 1.0) -> None:
        """Save as PNG image.
        
        Args:
            filename: The output filename (should end in .png).
            scale: Scale factor for the output (e.g., 2.0 for 2x resolution).
        
        Requires: pip install cairosvg
        """
        png_bytes = _svg_to_png_bytes(self.to_svg(), scale=scale)
        with open(filename, 'wb') as f:
            f.write(png_bytes)
    
    def save_jpeg(self, filename: str, scale: float = 1.0, quality: int = 90) -> None:
        """Save as JPEG image.
        
        Args:
            filename: The output filename (should end in .jpg or .jpeg).
            scale: Scale factor for the output (e.g., 2.0 for 2x resolution).
            quality: JPEG quality (1-100, default 90).
        
        Requires: pip install cairosvg Pillow
        """
        jpeg_bytes = _svg_to_jpeg_bytes(self.to_svg(), scale=scale, quality=quality)
        with open(filename, 'wb') as f:
            f.write(jpeg_bytes)
    
    def _repr_svg_(self) -> str:
        """IPython/Jupyter display hook for inline SVG rendering."""
        return self.to_svg()
    
    def __repr__(self) -> str:
        return f"Venndicon(size={self.size}, seed={self.seed})"


def generate(size: int = 500, seed: Optional[int] = None) -> Venndicon:
    """Generate a new Venndicon.
    
    Args:
        size: The width and height of the SVG in pixels.
        seed: Optional random seed for reproducible results.
    
    Returns:
        A Venndicon instance.
    """
    return Venndicon(size=size, seed=seed)


def generate_svg(size: int = 500, seed: Optional[int] = None) -> str:
    """Generate a Venndicon SVG string.
    
    Args:
        size: The width and height of the SVG in pixels.
        seed: Optional random seed for reproducible results.
    
    Returns:
        The SVG markup as a string.
    """
    return Venndicon(size=size, seed=seed).to_svg()


class VenndiconGrid:
    """A grid of Venndicon icons.
    
    Creates an SVG containing multiple Venndicons arranged in a grid.
    """
    
    def __init__(
        self,
        rows: int = 3,
        cols: int = 3,
        cell_size: int = 150,
        gap: int = 10,
        start_seed: Optional[int] = None,
        background: str = "#222222",
    ):
        """Initialize a VenndiconGrid.
        
        Args:
            rows: Number of rows in the grid.
            cols: Number of columns in the grid.
            cell_size: Size of each Venndicon cell in pixels.
            gap: Gap between cells in pixels.
            start_seed: Optional starting seed. If provided, seeds will be
                       sequential (start_seed, start_seed+1, ...). If None,
                       each icon will be randomly generated.
            background: Background color for the grid.
        """
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.gap = gap
        self.start_seed = start_seed
        self.background = background
        self._uid = uuid.uuid4().hex[:8]
        
        # Generate all the icons
        self.icons = []
        for i in range(rows * cols):
            seed = (start_seed + i) if start_seed is not None else None
            self.icons.append(Venndicon(size=cell_size, seed=seed))
    
    @property
    def width(self) -> int:
        """Total width of the grid SVG."""
        return self.cols * self.cell_size + (self.cols + 1) * self.gap
    
    @property
    def height(self) -> int:
        """Total height of the grid SVG."""
        return self.rows * self.cell_size + (self.rows + 1) * self.gap
    
    def to_svg(self) -> str:
        """Generate the grid SVG as a string.
        
        Returns:
            The SVG markup as a string.
        """
        dwg = svgwrite.Drawing(size=(self.width, self.height))
        
        # Background
        dwg.add(dwg.rect(insert=(0, 0), size=(self.width, self.height), fill=self.background))
        
        # Add each icon as a nested SVG
        for i, icon in enumerate(self.icons):
            row = i // self.cols
            col = i % self.cols
            
            x = self.gap + col * (self.cell_size + self.gap)
            y = self.gap + row * (self.cell_size + self.gap)
            
            # Create a group with transform to position the icon
            g = dwg.g(transform=f"translate({x}, {y})")
            
            # Parse the icon's SVG and add its elements
            # We need to add the defs and elements from each icon
            icon_svg = icon.to_svg()
            
            # Use nested SVG for proper clipping context
            nested = dwg.svg(insert=(x, y), size=(self.cell_size, self.cell_size))
            
            # Add clip path definitions from the icon
            icon_defs = dwg.defs
            uid = icon._uid
            
            # Clip paths
            clip2 = dwg.clipPath(id=f"clip2_{uid}")
            clip2.add(dwg.circle(center=(icon.cx2, icon.cy2), r=icon.cr2 / 2))
            icon_defs.add(clip2)
            
            clip3 = dwg.clipPath(id=f"clip3_{uid}")
            clip3.add(dwg.circle(center=(icon.cx3, icon.cy3), r=icon.cr3 / 2))
            icon_defs.add(clip3)
            
            clip3a = dwg.clipPath(id=f"clip3a_{uid}")
            clip3a.add(dwg.circle(center=(icon.cx3, icon.cy3), r=icon.cr3 / 2))
            icon_defs.add(clip3a)
            
            clip1 = dwg.clipPath(id=f"clip1_{uid}")
            clip1.add(dwg.circle(center=(icon.cx1, icon.cy1), r=icon.cr1 / 2))
            icon_defs.add(clip1)
            
            clip_triple = dwg.clipPath(id=f"clip_triple_{uid}")
            clip_triple['clip-path'] = f"url(#clip1_{uid})"
            clip_triple.add(dwg.circle(center=(icon.cx3, icon.cy3), r=icon.cr3 / 2))
            icon_defs.add(clip_triple)
            
            # Background rect for this cell
            nested.add(dwg.rect(insert=(0, 0), size=(icon.size, icon.size), fill=icon.background_color))
            
            # Circle 1
            nested.add(dwg.circle(center=(icon.cx1, icon.cy1), r=icon.cr1 / 2, fill=icon.circle1_color))
            
            # Circle 2
            nested.add(dwg.circle(center=(icon.cx2, icon.cy2), r=icon.cr2 / 2, fill=icon.circle2_color))
            
            # Circle 3
            nested.add(dwg.circle(center=(icon.cx3, icon.cy3), r=icon.cr3 / 2, fill=icon.circle3_color))
            
            # Intersection 1∩2
            ci12 = dwg.circle(center=(icon.cx1, icon.cy1), r=icon.cr1 / 2, fill=icon.intersection12_color)
            ci12['clip-path'] = f"url(#clip2_{uid})"
            nested.add(ci12)
            
            # Intersection 1∩3
            ci13 = dwg.circle(center=(icon.cx1, icon.cy1), r=icon.cr1 / 2, fill=icon.intersection13_color)
            ci13['clip-path'] = f"url(#clip3_{uid})"
            nested.add(ci13)
            
            # Intersection 2∩3
            ci23 = dwg.circle(center=(icon.cx2, icon.cy2), r=icon.cr2 / 2, fill=icon.intersection23_color)
            ci23['clip-path'] = f"url(#clip3a_{uid})"
            nested.add(ci23)
            
            # Triple intersection
            c123 = dwg.circle(center=(icon.cx2, icon.cy2), r=icon.cr2 / 2, fill=icon.intersection123_color)
            c123['clip-path'] = f"url(#clip_triple_{uid})"
            nested.add(c123)
            
            dwg.add(nested)
        
        return dwg.tostring()
    
    def save(self, filename: str) -> None:
        """Save the grid SVG to a file.
        
        Args:
            filename: The output filename (should end in .svg).
        """
        svg_content = self.to_svg()
        with open(filename, 'w') as f:
            f.write(svg_content)
    
    def save_png(self, filename: str, scale: float = 1.0) -> None:
        """Save as PNG image.
        
        Args:
            filename: The output filename (should end in .png).
            scale: Scale factor for the output (e.g., 2.0 for 2x resolution).
        
        Requires: pip install cairosvg
        """
        png_bytes = _svg_to_png_bytes(self.to_svg(), scale=scale)
        with open(filename, 'wb') as f:
            f.write(png_bytes)
    
    def save_jpeg(self, filename: str, scale: float = 1.0, quality: int = 90) -> None:
        """Save as JPEG image.
        
        Args:
            filename: The output filename (should end in .jpg or .jpeg).
            scale: Scale factor for the output (e.g., 2.0 for 2x resolution).
            quality: JPEG quality (1-100, default 90).
        
        Requires: pip install cairosvg Pillow
        """
        jpeg_bytes = _svg_to_jpeg_bytes(self.to_svg(), scale=scale, quality=quality)
        with open(filename, 'wb') as f:
            f.write(jpeg_bytes)
    
    def _repr_svg_(self) -> str:
        """IPython/Jupyter display hook for inline SVG rendering."""
        return self.to_svg()
    
    def __repr__(self) -> str:
        return f"VenndiconGrid(rows={self.rows}, cols={self.cols}, cell_size={self.cell_size})"


def grid(
    rows: int = 3,
    cols: int = 3,
    cell_size: int = 150,
    gap: int = 10,
    start_seed: Optional[int] = None,
    background: str = "#222222",
) -> VenndiconGrid:
    """Generate a grid of Venndicons.
    
    Args:
        rows: Number of rows in the grid.
        cols: Number of columns in the grid.
        cell_size: Size of each Venndicon cell in pixels.
        gap: Gap between cells in pixels.
        start_seed: Optional starting seed. If provided, seeds will be
                   sequential (start_seed, start_seed+1, ...). If None,
                   each icon will be randomly generated.
        background: Background color for the grid.
    
    Returns:
        A VenndiconGrid instance.
    
    Example:
        >>> from venndicon import grid
        >>> g = grid(rows=4, cols=6, cell_size=100, start_seed=0)
        >>> g.save("my_grid.svg")
    """
    return VenndiconGrid(
        rows=rows,
        cols=cols,
        cell_size=cell_size,
        gap=gap,
        start_seed=start_seed,
        background=background,
    )

