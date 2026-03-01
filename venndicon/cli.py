"""Command-line interface for matching Venndicons to images."""

import argparse
import json
import os
import sys

from .core import match_venndicons_to_image


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate Venndicon grids that match the "
            "colours of input images."
        ),
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="One or more image files to match against.",
    )
    parser.add_argument(
        "--cols", type=int, default=50,
        help="Number of columns in the grid (for the "
             "first image; others auto-scale). "
             "Default: 50",
    )
    parser.add_argument(
        "--rows", type=int, default=50,
        help="Number of rows in the grid (for the "
             "first image; others auto-scale). "
             "Default: 50",
    )
    parser.add_argument(
        "--cell-size", type=int, default=10,
        help="Pixel size of each Venndicon cell. Default: 10",
    )
    parser.add_argument(
        "--start-seed", type=int, default=0,
        help="Starting seed for reproducible Venndicon generation. Default: 0",
    )
    parser.add_argument(
        "--no-image-colors", action="store_true",
        help="Disable sampling Venndicon colours from the image palette.",
    )
    parser.add_argument(
        "--gap", type=int, default=0,
        help="Gap between cells in the output grid (pixels). Default: 0",
    )
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Scale factor for raster output "
             "(e.g. 2.0 for 2x resolution). Default: 1.0",
    )
    parser.add_argument(
        "--quality", type=int, default=90,
        help="JPEG quality (1-100). Default: 90",
    )
    parser.add_argument(
        "--format", choices=["jpeg", "png", "svg"], default="svg",
        help="Output file format. Default: svg",
    )
    parser.add_argument(
        "--output-dir", default=".",
        help="Directory for output files. Default: current directory",
    )
    parser.add_argument(
        "--prefix", default="matched_",
        help="Filename prefix for output files. Default: 'matched_'",
    )
    parser.add_argument(
        "--background", default="#222222",
        help="Grid background colour (hex). Default: #222222",
    )

    args = parser.parse_args()

    for path in args.images:
        if not os.path.isfile(path):
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)

    use_image_colors = not args.no_image_colors

    print(f"Matching {len(args.images)} image(s)  "
          f"cols={args.cols} rows={args.rows} "
          f"cell_size={args.cell_size} "
          f"seed={args.start_seed} "
          f"image_colors={use_image_colors}",
          file=sys.stderr)

    if len(args.images) == 1:
        results = [match_venndicons_to_image(
            args.images[0],
            cols=args.cols,
            rows=args.rows,
            start_seed=args.start_seed,
            cell_size=args.cell_size,
            use_image_colors=use_image_colors,
        )]
    else:
        results = match_venndicons_to_image(
            args.images,
            cols=args.cols,
            rows=args.rows,
            start_seed=args.start_seed,
            cell_size=args.cell_size,
            use_image_colors=use_image_colors,
        )

    ext = {"jpeg": ".jpg", "png": ".png", "svg": ".svg"}[args.format]

    for image_path, result in zip(args.images, results):
        base = os.path.splitext(os.path.basename(image_path))[0]
        out_name = f"{args.prefix}{base}{ext}"
        out_path = os.path.join(args.output_dir, out_name)

        grid = result.to_grid(gap=args.gap, background=args.background)

        if args.format == "svg":
            grid.save(out_path)
        elif args.format == "png":
            grid.save_png(out_path, scale=args.scale)
        else:
            grid.save_jpeg(out_path, scale=args.scale, quality=args.quality)

        print(f"  {result.cols}x{result.rows} grid -> {out_path}",
              file=sys.stderr)

    # Build coordinate mapping: for each venndicon that appears in
    # the first image (iterated in grid order), list its (col, row)
    # position in every image.  None when the venndicon wasn't used.
    image_meta = []
    position_maps = []
    for image_path, result in zip(args.images, results):
        base = os.path.splitext(os.path.basename(image_path))[0]
        out_name = f"{args.prefix}{base}{ext}"
        image_meta.append({
            "file": out_name,
            "cols": result.cols,
            "rows": result.rows,
            "cell_size": args.cell_size,
            "gap": args.gap,
        })
        pm = {}
        for v_idx, c_idx in result.assignment:
            col = c_idx % result.cols
            row = c_idx // result.cols
            pm[v_idx] = [col, row]
        position_maps.append(pm)

    coordinates = []
    for v_idx, _ in results[0].assignment:
        entry = []
        for pm in position_maps:
            entry.append(pm.get(v_idx))
        coordinates.append(entry)

    manifest = {
        "images": image_meta,
        "coordinates": coordinates,
    }
    print(json.dumps(manifest))
    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
