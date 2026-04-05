"""KiCad IPC API plugin: place footprints at Ergogen switch positions."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Annotated

import typer
from kipy import KiCad
from kipy.board_types import FootprintInstance
from kipy.geometry import Angle, Vector2
from kipy.util.units import from_mm

if TYPE_CHECKING:
    from pathlib import Path

    from kipy.board import Board

app = typer.Typer()


def find_template(board: Board, library: str, footprint_name: str) -> FootprintInstance:
    """Find an existing footprint on the board to use as a clone template."""
    for fp in board.get_footprints():
        fp_id = fp.definition.id
        if fp_id.library == library and fp_id.name == footprint_name:
            return fp

    msg = (
        f"No {library}:{footprint_name} footprint found on the board. "
        f"Place one instance manually first (Place → Add Footprint), "
        f"then re-run this command."
    )
    raise typer.BadParameter(msg)


def place_footprints(
    board: Board,
    points: dict,
    template: FootprintInstance,
) -> int:
    """Clone a template footprint to every Ergogen key position on the board."""
    commit = board.begin_commit()

    clones = []
    for point in points.values():
        clone = FootprintInstance(template.proto)
        clone._proto.id.value = ""  # noqa: SLF001
        clone.position = Vector2.from_xy(from_mm(point["x"]), from_mm(-point["y"]))
        clone.orientation = Angle.from_degrees(point["r"])
        clones.append(clone)

    created = board.create_items(clones)

    for i, (fp, name) in enumerate(zip(created, points.keys(), strict=True), start=1):
        fp.reference_field.text.value = f"K{i}"
        fp.value_field.text.value = name
    board.update_items(created)

    board.push_commit(commit, "Place Ergogen footprints")
    return len(created)


@app.command()
def main(
    points_json: Annotated[
        Path,
        typer.Argument(help="Path to Ergogen points JSON file", exists=True),
    ],
    footprint: Annotated[
        str,
        typer.Argument(help="Footprint in Library:Name format"),
    ],
) -> None:
    """Place a KiCad footprint at every Ergogen key position.

    Requires one instance of the footprint already on the board as a template.
    """
    if ":" not in footprint:
        msg = f"Expected Library:Name format, got: {footprint!r}"
        raise typer.BadParameter(msg)
    library, fp_name = footprint.split(":", 1)

    with points_json.open() as f:
        points = json.load(f)

    kicad = KiCad()
    board = kicad.get_board()
    template = find_template(board, library, fp_name)
    count = place_footprints(board, points, template)

    print(f"Placed {count} footprints on {board.name}.")


if __name__ == "__main__":
    app()
