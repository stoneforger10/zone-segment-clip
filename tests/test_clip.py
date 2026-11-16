import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "contracts/ZoneSegmentClip.py"
ZONE = "CAZ006"
URL = "https://api.weather.gov/zones/forecast/" + ZONE


def feature(rings, zone=ZONE):
    return json.dumps({"id": URL[:-6] + zone, "type": "Feature",
                       "geometry": {"type": "Polygon", "coordinates": rings}}).encode()


SQUARE = [[-124, 36], [-122, 36], [-122, 40], [-124, 40], [-124, 36]]
HOLE = [[-123.5, 37], [-123.5, 39], [-122.5, 39], [-122.5, 37], [-123.5, 37]]


@pytest.fixture
def clipper(direct_deploy):
    contract = direct_deploy(str(CODE))
    return contract, sys.modules[type(contract._instance).__module__]


@pytest.mark.parametrize("rings,start,end,expected,contacts,covered", [
    ([SQUARE, HOLE], [-125, 38], [-121, 38], [
        ["0/1", "1/4", "outside"], ["1/4", "3/8", "inside"],
        ["3/8", "5/8", "outside"], ["5/8", "3/4", "inside"], ["3/4", "1/1", "outside"],
    ], ["1/4", "3/8", "5/8", "3/4"], "1/4"),
    ([SQUARE], [-125, 36], [-121, 36], [
        ["0/1", "1/4", "outside"], ["1/4", "3/4", "boundary"], ["3/4", "1/1", "outside"],
    ], ["1/4", "3/4"], "0/1"),
    ([SQUARE], [-125, 37], [-123, 35], [
        ["0/1", "1/1", "outside"],
    ], ["1/2"], "0/1"),
    ([SQUARE], [-123, 41], [-123, 37], [
        ["0/1", "1/4", "outside"], ["1/4", "1/1", "inside"],
    ], ["1/4"], "3/4"),
])
def test_exact_intersections(clipper, rings, start, end, expected, contacts, covered):
    _, mod = clipper
    geometry = mod.parse_geometry(feature(rings), ZONE)
    a, b = [[n * 1_000_000 for n in xy] for xy in (start, end)]
    report = mod.clip_report(ZONE, geometry, a, b)
    assert (report["runs"], report["contacts"], report["inside_fraction"]) == (expected, contacts, covered)


@pytest.mark.parametrize("body", [
    feature([SQUARE[:-1]]),
    feature([SQUARE], "AZZ001"),
    feature([[[-124, 36], [-123, 36], [-122, 36], [-124, 36]]]),
    feature([[[-124, 36], [-122.0000001, 36], [-122, 40], [-124, 36]]]),
    b'{"id":null,"id":"duplicate"}',
])
def test_malformed_geometry_rejected(clipper, body):
    _, mod = clipper
    with pytest.raises(ValueError):
        mod.parse_geometry(body, ZONE)


def test_direct_validator_recomputes_geometry_and_same_clip_is_idempotent(clipper, direct_vm):
    contract, mod = clipper
    def mock(body):
        direct_vm.clear_mocks()
        direct_vm.mock_web(URL, {"method": "GET", "response": {"status": 200, "headers": {}, "body": body}})
    mock(feature([SQUARE, HOLE]))
    segment = [[-125000000, 38000000], [-121000000, 38000000]]
    key = contract.clip(ZONE, segment)
    report = contract.get_clip(key)
    assert report["inside_fraction"] == "1/4"
    assert contract.clip(ZONE, segment) == key
    assert direct_vm.run_validator()
    forged = {**report, "inside_fraction": "1/2"}
    assert not direct_vm.run_validator(leader_result=mod.canonical(forged))
    mock(feature([SQUARE]))
    assert not direct_vm.run_validator()
    assert contract.get_clip(key) == report


def test_degenerate_segment_is_rejected_before_web(clipper, direct_vm):
    contract, _ = clipper
    with direct_vm.expect_revert("endpoints must differ"):
        contract.clip(ZONE, [[-125000000, 38000000], [-125000000, 38000000]])


def test_publisher_feature_against_independent_scanline_if_cached(clipper, direct_vm):
    cached = ROOT / ".gltest_cache" / (ZONE + ".json")
    if not cached.is_file():
        pytest.skip("Download the referenced CAZ006 feature for the full geometry check")
    reference = json.loads((ROOT / "REFERENCE.json").read_text(encoding="utf-8"))
    contract, _ = clipper
    direct_vm.mock_web(URL, {"method": "GET", "response": {
        "status": 200, "headers": {}, "body": cached.read_bytes(),
    }})
    for expected in reference["cases"].values():
        key = contract.clip(ZONE, expected["segment_microdegrees"])
        assert contract.get_clip(key) == expected
