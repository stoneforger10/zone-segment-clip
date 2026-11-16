"""Build the CAZ006 proof vectors by horizontal scanline rather than general clipping."""
import hashlib
import json
import sys
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
from pathlib import Path


source = Path(sys.argv[1]).read_bytes()
doc = json.loads(source, parse_float=Decimal)
zone = "CAZ006"
url = "https://api.weather.gov/zones/forecast/" + zone
assert doc["id"] == url and doc["geometry"]["type"] == "MultiPolygon"
geometry = []
for polygon in doc["geometry"]["coordinates"]:
    rings = []
    for ring in polygon:
        cleaned = []
        for pair in ring:
            values = [Decimal(q) * 1000000 for q in pair]
            assert all(n == int(n) for n in values)
            vertex = list(map(int, values))
            if not cleaned or vertex != cleaned[-1]:
                cleaned.append(vertex)
        rings.append(cleaned)
    geometry.append(rings)
polygon_hash = hashlib.sha256(json.dumps(geometry, separators=(",", ":")).encode()).hexdigest()


def rational(n):
    return f"{n.numerator}/{n.denominator}"


def report(segment, runs, contacts, inside):
    return {"zone": zone, "source_url": url, "geometry_sha256": polygon_hash,
            "segment_microdegrees": segment, "runs": runs, "contacts": contacts,
            "inside_fraction": inside}


def horizontal(y):
    left, right = -124000000, -122000000
    dx = right - left
    events = defaultdict(list)
    for index, poly in enumerate(geometry):
        for ring in poly:
            for (a, ya), (b, yb) in zip(ring, ring[1:]):
                assert y != ya and y != yb
                if (ya < y) != (yb < y):
                    x = Fraction(a) + Fraction((y - ya) * (b - a), yb - ya)
                    assert left < x < right
                    events[(x - left) / dx].append(index)
    inside_polygons = set()
    previous = Fraction(0)
    runs, inside = [], Fraction(0)
    for mark in sorted(events.keys() | {Fraction(1)}):
        label = "inside" if inside_polygons else "outside"
        if inside_polygons:
            inside += mark - previous
        if runs and runs[-1][2] == label:
            runs[-1][1] = rational(mark)
        else:
            runs.append([rational(previous), rational(mark), label])
        for index in events[mark]:
            inside_polygons.symmetric_difference_update({index})
        previous = mark
    assert not inside_polygons
    return report([[left, y], [right, y]], runs, list(map(rational, sorted(events.keys() - {Fraction(1)}))),
                  rational(inside))


traverse = horizontal(37770001)
outside = horizontal(39000001)
assert any(span[2] == "inside" for span in traverse["runs"])
assert outside["runs"] == [["0/1", "1/1", "outside"]]
first_edge = geometry[0][0][:2]
for poly in geometry[1:]:
    assert any(
        max(p[axis] for p in first_edge) < min(p[axis] for p in poly[0])
        or min(p[axis] for p in first_edge) > max(p[axis] for p in poly[0])
        for axis in (0, 1)
    ), "Boundary example intersects another polygon's bounding box"
assert len(geometry[0]) == 1
boundary = report(first_edge, [["0/1", "1/1", "boundary"]], ["0/1", "1/1"], "0/1")
Path("REFERENCE.json").write_text(json.dumps(
    {"source_body_sha256": hashlib.sha256(source).hexdigest(),
     "cases": {"traverse": traverse, "outside": outside, "boundary": boundary}}, indent=2) + "\n", encoding="utf-8")
