"""Core Venndicon SVG generation logic."""

import io
import random
import uuid
from typing import Optional
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

