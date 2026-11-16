#!/usr/bin/env python3
"""
Geometrically scale a crowdit scenario by a given percentage.

Usage:
    python scale_scenario.py <crowdit_file> <scale_percent> [--inplace | --output <dir>]

Arguments:
    crowdit_file   Path to the .crowdit file
    scale_percent  Scale percentage (e.g., 70 for 70% = factor 0.7)
    --inplace      Modify files in place (default: create new files with _<pct>pct suffix)
    --output <dir> Output directory for the scaled scenario

What gets scaled:
    - All <point x="..." y="..."/> coordinates in floor geometry files
    - All <point x="..." y="..."/> coordinates in measurement rectangles (.crowdit)

What is NOT scaled:
    - Pedestrian properties: velocity, torsoSize, perceptionRadius  (agent physics)
    - Time values: intervals, premovement distributions
    - Pedestrian counts (howMany)
    - Floor height / elevation
    - The 'out' output folder inside _res
    - cellDist in <floorProp> (grid cell resolution)
    - distBetweenTwoPts in <settings> (agent locomotion step size)

"""

from __future__ import annotations

import sys
import re
import shutil
import argparse
from pathlib import Path


def scale_num(value_str: str, factor: float) -> str:
    """Scale a numeric string by factor, preserving up to 15 significant digits."""
    return f"{float(value_str) * factor:.15g}"


def scale_point_tags(content: str, factor: float) -> str:
    """Scale all <point x="..." y="..."/> self-closing elements in XML content."""
    def replace_point(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'x="([^"]+)"', lambda n: f'x="{scale_num(n.group(1), factor)}"', tag)
        tag = re.sub(r'y="([^"]+)"', lambda n: f'y="{scale_num(n.group(1), factor)}"', tag)
        return tag

    return re.sub(r'<point\b[^>]*/>', replace_point, content)


def scale_attribute(content: str, attr_name: str, factor: float) -> str:
    """Scale a single named XML attribute value by factor."""
    return re.sub(
        rf'{re.escape(attr_name)}="([^"]+)"',
        lambda m: f'{attr_name}="{scale_num(m.group(1), factor)}"',
        content,
    )


def scale_crowdit_content(content: str, factor: float) -> str:
    """Scale all geometry-relevant values in a .crowdit file content string."""
    content = scale_point_tags(content, factor)
    return content


def scale_floor_content(content: str, factor: float) -> str:
    """Scale all geometry-relevant values in a .floor file content string."""
    return scale_point_tags(content, factor)


def scale_scenario(
    crowdit_path: Path,
    scale_percent: float,
    inplace: bool = False,
    output_dir: Path | None = None,
) -> None:
    factor = scale_percent / 100.0
    res_dir = crowdit_path.parent / (crowdit_path.stem + "_res")

    if not res_dir.is_dir():
        print(f"Warning: _res directory not found at {res_dir}", file=sys.stderr)

    # Determine output paths
    if inplace:
        out_crowdit = crowdit_path
        out_res = res_dir
    elif output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_crowdit = output_dir / crowdit_path.name
        out_res = output_dir / res_dir.name
        if out_res.exists():
            shutil.rmtree(out_res)
        if res_dir.is_dir():
            shutil.copytree(res_dir, out_res, ignore=shutil.ignore_patterns("out"))
    else:
        pct_label = f"_{int(scale_percent)}pct"
        out_crowdit = crowdit_path.parent / (crowdit_path.stem + pct_label + crowdit_path.suffix)
        out_res = crowdit_path.parent / (crowdit_path.stem + pct_label + "_res")
        if out_res.exists():
            shutil.rmtree(out_res)
        if res_dir.is_dir():
            shutil.copytree(res_dir, out_res, ignore=shutil.ignore_patterns("out"))

    # Scale floor files (geometry/*.floor)
    if res_dir.is_dir():
        src_geom = res_dir / "geometry"
        dst_geom = out_res / "geometry"
        for floor_file in src_geom.glob("*.floor"):
            content = floor_file.read_text(encoding="utf-8")
            scaled = scale_floor_content(content, factor)
            (dst_geom / floor_file.name).write_text(scaled, encoding="utf-8")

    # Scale .crowdit file
    content = crowdit_path.read_text(encoding="utf-8")
    out_crowdit.write_text(scale_crowdit_content(content, factor), encoding="utf-8")

    print(f"Scaled {scale_percent}% -> {out_crowdit}")
    if not inplace:
        print(f"           -> {out_res}/")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("crowdit_file", type=Path, help="Path to the .crowdit file")
    parser.add_argument(
        "scale_percent",
        type=float,
        help="Scale percentage (e.g., 70 for 70%%)",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--inplace",
        action="store_true",
        help="Modify files in place instead of creating a copy",
    )
    group.add_argument(
        "--output",
        type=Path,
        metavar="DIR",
        help="Output directory for the scaled scenario",
    )
    args = parser.parse_args()

    if not args.crowdit_file.exists():
        print(f"Error: {args.crowdit_file} not found", file=sys.stderr)
        sys.exit(1)

    scale_scenario(
        args.crowdit_file,
        args.scale_percent,
        inplace=args.inplace,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
