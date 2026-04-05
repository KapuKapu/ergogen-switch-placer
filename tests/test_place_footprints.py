"""Tests for place_footprints.py."""

import json
from pathlib import Path

import pytest

try:
    import pcbnew
except ImportError:
    pcbnew = None

pytestmark = pytest.mark.skipif(pcbnew is None, reason="pcbnew (KiCad) not available")

from ergogen_key_placer.place_footprints import place_footprints

SCRIPTS_DIR = Path(__file__).parent
FIXTURES_DIR = SCRIPTS_DIR / "fixtures"
TOLERANCE_MM = 0.001

CASES = [
    (FIXTURES_DIR / "points.json", FIXTURES_DIR / "Kailh_socket_PG1350.kicad_mod"),
]


def case_id(val):
    if isinstance(val, tuple):
        return f"{val[0].stem}+{val[1].stem}"
    return str(val)


@pytest.fixture(params=CASES, ids=case_id, scope="session")
def board_and_points(request, tmp_path_factory):
    points_path, footprint_path = request.param
    with open(points_path) as f:
        points = json.load(f)
    output = tmp_path_factory.mktemp("pcb") / "output.kicad_pcb"
    place_footprints(points_path, footprint_path, output)
    board = pcbnew.LoadBoard(str(output))
    return board, points


def test_footprint_count(board_and_points):
    board, points = board_and_points
    assert len(board.GetFootprints()) == len(points)


def test_positions_and_rotations(board_and_points):
    board, points = board_and_points
    fp_by_value = {fp.GetValue(): fp for fp in board.GetFootprints()}

    for name, point in points.items():
        assert name in fp_by_value, f"Missing footprint for key '{name}'"
        fp = fp_by_value[name]

        actual_x = pcbnew.ToMM(fp.GetPosition().x)
        actual_y = pcbnew.ToMM(fp.GetPosition().y)
        actual_r = fp.GetOrientationDegrees()

        assert actual_x == pytest.approx(point["x"], abs=TOLERANCE_MM)
        assert actual_y == pytest.approx(-point["y"], abs=TOLERANCE_MM)
        assert actual_r == pytest.approx(point["r"], abs=TOLERANCE_MM)


def test_references_are_unique(board_and_points):
    board, _ = board_and_points
    refs = [fp.GetReference() for fp in board.GetFootprints()]
    assert len(refs) == len(set(refs))


def test_footprints_have_pads(board_and_points):
    board, _ = board_and_points
    for fp in board.GetFootprints():
        assert len(fp.Pads()) > 0, (
            f"{fp.GetReference()} ({fp.GetValue()}) has no pads"
        )
