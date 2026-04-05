#!/usr/bin/env python
"""Place a KiCad footprint at every key position from Ergogen points."""

import json
from pathlib import Path

import typer


def place_footprints(points_path: Path, footprint_path: Path, output_path: Path):
    import pcbnew

    footprint_path = footprint_path.resolve()

    with open(points_path) as f:
        points = json.load(f)

    lib_path = str(footprint_path.parent)
    fp_name = footprint_path.stem

    board = pcbnew.CreateEmptyBoard()

    for i, (name, point) in enumerate(points.items(), start=1):
        fp = pcbnew.FootprintLoad(lib_path, fp_name)

        kicad_x = point["x"]
        kicad_y = -point["y"]
        rotation = point["r"]

        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(kicad_x), pcbnew.FromMM(kicad_y)))
        fp.SetOrientationDegrees(rotation)
        fp.SetReference(f"K{i}")
        fp.SetValue(name)

        board.Add(fp)

    board.Save(str(output_path))
    print(f"Placed {len(points)} footprints -> {output_path}")


app = typer.Typer()


@app.command()
def main(
    points_path: Path = typer.Argument(help="Ergogen points JSON file"),
    footprint_path: Path = typer.Argument(help="KiCad footprint (.kicad_mod) file"),
    output_path: Path = typer.Argument(
        default=Path("placed.kicad_pcb"), help="Output .kicad_pcb path"
    ),
):
    """Place a KiCad footprint at every key position from Ergogen points."""
    place_footprints(points_path, footprint_path, output_path)


if __name__ == "__main__":
    app()
