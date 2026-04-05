"""Tests for kicad-plugin/action.py."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# wx requires KiCad's bundled wxPython; mock it so we can import the plugin module.
sys.modules.setdefault("wx", MagicMock())

_plugin_dir = str(Path(__file__).resolve().parent.parent / "kicad-plugin")
if _plugin_dir not in sys.path:
    sys.path.insert(0, _plugin_dir)

try:
    from action import parse_footprint_id, place_footprints
    from kipy.geometry import Angle, Vector2
    from kipy.util.units import from_mm
except ImportError:
    pytest.skip("kicad-python not available", allow_module_level=True)

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
with (FIXTURES_DIR / "points.json").open() as _f:
    POINTS = json.load(_f)


# ---------------------------------------------------------------------------
# parse_footprint_id
# ---------------------------------------------------------------------------


class TestParseFootprintId:
    def test_valid(self):
        assert parse_footprint_id("MyLib:MyCmp") == ("MyLib", "MyCmp")

    def test_colon_in_name(self):
        assert parse_footprint_id("Lib:Name:Extra") == ("Lib", "Name:Extra")

    def test_no_colon(self):
        with pytest.raises(ValueError, match="Expected Library:Name"):
            parse_footprint_id("NoColon")

    def test_empty_library(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_footprint_id(":Name")

    def test_empty_name(self):
        with pytest.raises(ValueError, match="non-empty"):
            parse_footprint_id("Lib:")

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Expected Library:Name"):
            parse_footprint_id("")


# ---------------------------------------------------------------------------
# place_footprints
# ---------------------------------------------------------------------------


def _mock_board(num_items):
    board = MagicMock()
    created = [MagicMock() for _ in range(num_items)]
    board.create_items.return_value = created
    return board, created


class TestPlaceFootprints:
    def test_returns_count(self):
        board, _ = _mock_board(len(POINTS))
        assert place_footprints(board, POINTS, "Lib", "Fp") == len(POINTS)

    def test_empty_points(self):
        board, _ = _mock_board(0)
        assert place_footprints(board, {}, "Lib", "Fp") == 0

    def test_commit_lifecycle(self):
        board, _ = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        board.begin_commit.assert_called_once()

    def test_creates_correct_number_of_items(self):
        board, _ = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        items = board.create_items.call_args[0][0]
        assert len(items) == len(POINTS)

    def test_footprint_definition(self):
        board, _ = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "MyLib", "MyCmp")

        items = board.create_items.call_args[0][0]
        for fp in items:
            assert fp.definition.id.library == "MyLib"
            assert fp.definition.id.name == "MyCmp"

    def test_positions(self):
        board, _ = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        items = board.create_items.call_args[0][0]
        for fp, point in zip(items, POINTS.values(), strict=True):
            expected = Vector2.from_xy(from_mm(point["x"]), from_mm(-point["y"]))
            assert fp.position == expected

    def test_orientations(self):
        board, _ = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        items = board.create_items.call_args[0][0]
        for fp, point in zip(items, POINTS.values(), strict=True):
            assert fp.orientation == Angle.from_degrees(point["r"])

    def test_references(self):
        board, created = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        for i, fp in enumerate(created, start=1):
            assert fp.reference_field.text.value == f"K{i}"

    def test_values_match_key_names(self):
        board, created = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        for fp, name in zip(created, POINTS.keys(), strict=True):
            assert fp.value_field.text.value == name

    def test_update_items_called_with_created(self):
        board, created = _mock_board(len(POINTS))
        place_footprints(board, POINTS, "Lib", "Fp")

        board.update_items.assert_called_once_with(created)
