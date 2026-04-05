"""KiCad IPC API plugin: place footprints at Ergogen switch positions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import wx
from kipy import KiCad
from kipy.board_types import FootprintInstance
from kipy.geometry import Angle, Vector2
from kipy.util.units import from_mm

if TYPE_CHECKING:
    from kipy.board import Board


class PlacerDialog(wx.Dialog):
    def __init__(self, parent: wx.Window | None = None) -> None:
        super().__init__(parent, title="Ergogen Key Placer")

        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(2, 2, 8, 8)
        grid.AddGrowableCol(1, 1)

        grid.Add(
            wx.StaticText(self, label="Points JSON:"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.points_picker = wx.FilePickerCtrl(
            self, wildcard="JSON files (*.json)|*.json"
        )
        grid.Add(self.points_picker, 1, wx.EXPAND)

        grid.Add(
            wx.StaticText(self, label="Footprint:"),
            0,
            wx.ALIGN_CENTER_VERTICAL,
        )
        self.fp_input = wx.TextCtrl(self, size=(300, -1))
        self.fp_input.SetHint("Library:Footprint")
        grid.Add(self.fp_input, 1, wx.EXPAND)

        sizer.Add(grid, 0, wx.EXPAND | wx.ALL, 12)

        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizerAndFit(sizer)


def parse_footprint_id(fp_id: str) -> tuple[str, str]:
    """Parse 'Library:Name' into (library, name)."""
    if ":" not in fp_id:
        msg = f"Expected Library:Name format, got: {fp_id!r}"
        raise ValueError(msg)
    library, name = fp_id.split(":", 1)
    if not library or not name:
        msg = f"Library and name must both be non-empty: {fp_id!r}"
        raise ValueError(msg)
    return library, name


def place_footprints(
    board: Board,
    points: dict,
    library: str,
    footprint_name: str,
) -> int:
    """Place a footprint at every Ergogen key position on the board."""
    commit = board.begin_commit()

    items = []
    for point in points.values():
        fp = FootprintInstance()
        fp.definition.id.library = library
        fp.definition.id.name = footprint_name
        fp.position = Vector2.from_xy(from_mm(point["x"]), from_mm(-point["y"]))
        fp.orientation = Angle.from_degrees(point["r"])
        items.append(fp)

    created = board.create_items(items)

    for i, (fp, name) in enumerate(zip(created, points.keys(), strict=True), start=1):
        fp.reference_field.text.value = f"K{i}"
        fp.value_field.text.value = name
    board.update_items(created)

    board.push_commit(commit, "Places Ergogen footprints")
    return len(created)


if __name__ == "__main__":
    app = wx.App()
    dlg = PlacerDialog()

    if dlg.ShowModal() == wx.ID_OK:
        points_path = dlg.points_picker.GetPath()
        fp_id = dlg.fp_input.GetValue().strip()

        if not points_path:
            wx.MessageBox("Select a points JSON file.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            try:
                library, fp_name = parse_footprint_id(fp_id)
                with Path(points_path).open() as f:
                    points = json.load(f)

                kicad = KiCad()
                board = kicad.get_board()
                count = place_footprints(board, points, library, fp_name)

                wx.MessageBox(
                    f"Placed {count} footprints.",
                    "Ergogen Swtich Placer",
                    wx.OK | wx.ICON_INFORMATION,
                )
            except Exception as e:  # noqa: BLE001
                wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)

    dlg.Destroy()
