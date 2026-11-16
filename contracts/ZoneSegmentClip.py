# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import hashlib
import json
import re
from decimal import Decimal, DecimalException
from fractions import Fraction

from genlayer import TreeMap, gl

BASE = "https://api.weather.gov/zones/forecast/"
HEADERS = {"Accept": "application/geo+json", "User-Agent": "ZoneSegmentClip/1.0"}
ONE = 1_000_000
MAX_VERTICES = 6000
MAX_CUTS = 64


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(text):
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def unique_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def point(value):
    if not isinstance(value, list) or len(value) != 2 or any(type(n) is not int for n in value):
        raise ValueError("Expected a longitude and latitude pair in integer microdegrees")
    x, y = value
    if not -130 * ONE <= x <= -60 * ONE or not 20 * ONE <= y <= 55 * ONE:
        raise ValueError("Coordinates outside supported continental extent")
    return x, y


def microdegrees(value):
    if type(value) not in (int, Decimal) or not -130 <= value <= 55:
        raise ValueError("Non-numeric or out-of-range GeoJSON coordinate")
    if isinstance(value, Decimal) and value.as_tuple().exponent < -18:
        raise ValueError("Excessive coordinate precision")
    exact = Fraction(value) * ONE
    if exact.denominator != 1:
        raise ValueError("GeoJSON coordinate exceeds six decimal places")
    return exact.numerator


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def vector(a, b):
    return (b[0] - a[0], b[1] - a[1])


def parse_geometry(body, zone):
    if not isinstance(body, bytes) or not 0 < len(body) <= 1_000_000:
        raise ValueError("Missing or oversized NWS response")
    doc = json.loads(body, parse_float=Decimal, object_pairs_hook=unique_keys)
    if not isinstance(doc, dict) or doc.get("id") != BASE + zone or doc.get("type") != "Feature":
        raise ValueError("Unexpected NWS feature")
    raw = doc.get("geometry")
    if not isinstance(raw, dict) or raw.get("type") not in ("Polygon", "MultiPolygon"):
        raise ValueError("Unsupported NWS geometry")
    coordinates = raw.get("coordinates")
    polygons = [coordinates] if raw["type"] == "Polygon" else coordinates
    if not isinstance(polygons, list) or not 1 <= len(polygons) <= 64:
        raise ValueError("Too many or missing polygons")
    out, count = [], 0
    for poly in polygons:
        if not isinstance(poly, list) or not 1 <= len(poly) <= 64:
            raise ValueError("Invalid polygon rings")
        rings = []
        for raw_ring in poly:
            if not isinstance(raw_ring, list) or len(raw_ring) < 4:
                raise ValueError("Invalid ring")
            count += len(raw_ring)
            if count > MAX_VERTICES:
                raise ValueError("Too many polygon vertices")
            ring = []
            for pair in raw_ring:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError("Invalid GeoJSON position")
                xy = point([microdegrees(n) for n in pair])
                if not ring or xy != ring[-1]:
                    ring.append(xy)
            if len(ring) < 4 or ring[0] != ring[-1] or sum(cross(a, b) for a, b in zip(ring, ring[1:])) == 0:
                raise ValueError("Unclosed or degenerate ring")
            rings.append(ring)
        out.append(rings)
    return out


def intersection(start, delta, a, b):
    edge, offset = vector(a, b), vector(start, a)
    determinant = cross(delta, edge)
    if determinant:
        position = Fraction(cross(offset, edge), determinant)
        edge_position = Fraction(cross(offset, delta), determinant)
        if 0 <= position <= 1 and 0 <= edge_position <= 1:
            return (position,)
        return ()
    if cross(offset, delta):
        return ()
    axis = 0 if delta[0] else 1
    first = Fraction(a[axis] - start[axis], delta[axis])
    last = Fraction(b[axis] - start[axis], delta[axis])
    left = max(Fraction(0), min(first, last))
    right = min(Fraction(1), max(first, last))
    return (left, right) if left <= right else ()


def ring_location(ring, x, y, n):
    inside = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:]):
        ax, ay, bx, by = ax * n, ay * n, bx * n, by * n
        if not min(ay, by) <= y <= max(ay, by):
            continue
        side = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
        if side == 0 and min(ax, bx) <= x <= max(ax, bx):
            return "boundary"
        if ((ay > y) != (by > y)) and ((side > 0) == (by > ay)):
            inside = not inside
    return "inside" if inside else "outside"


def location(polygons, start, delta, t):
    n = t.denominator
    x = start[0] * n + delta[0] * t.numerator
    y = start[1] * n + delta[1] * t.numerator
    boundary = False
    for exterior, *holes in polygons:
        status = ring_location(exterior, x, y, n)
        if status == "outside":
            continue
        hole_locations = [ring_location(hole, x, y, n) for hole in holes]
        if status == "inside" and all(label == "outside" for label in hole_locations):
            return "inside"
        if status == "boundary" or "boundary" in hole_locations:
            boundary = True
    return "boundary" if boundary else "outside"


def fraction_text(value):
    return f"{value.numerator}/{value.denominator}"


def clip_report(zone, polygons, start, end):
    delta = vector(start, end)
    contacts = set()
    for poly in polygons:
        for ring in poly:
            for a, b in zip(ring, ring[1:]):
                contacts.update(intersection(start, delta, a, b))
                if len(contacts) > MAX_CUTS:
                    raise ValueError("Too many intersections for one clip")
    cuts = sorted(contacts | {Fraction(0), Fraction(1)})
    runs = []
    for lo, hi in zip(cuts, cuts[1:]):
        label = location(polygons, start, delta, (lo + hi) / 2)
        if runs and runs[-1][2] == label:
            runs[-1][1] = hi
        else:
            runs.append([lo, hi, label])
    return {
        "zone": zone,
        "source_url": BASE + zone,
        "geometry_sha256": digest(canonical(polygons)),
        "segment_microdegrees": [list(start), list(end)],
        "runs": [[fraction_text(lo), fraction_text(hi), label] for lo, hi, label in runs],
        "contacts": [fraction_text(t) for t in sorted(contacts)],
        "inside_fraction": fraction_text(sum((hi - lo for lo, hi, label in runs if label == "inside"), Fraction(0))),
    }


class ZoneSegmentClip(gl.Contract):
    clips: TreeMap[str, str]

    def __init__(self):
        pass

    @gl.public.write
    def clip(self, zone: str, segment: list[list[int]]) -> str:
        if not re.fullmatch(r"[A-Z]{2}Z[0-9]{3}", zone):
            raise gl.vm.UserError("Invalid forecast zone or segment")
        if not isinstance(segment, list) or len(segment) != 2:
            raise gl.vm.UserError("Expected two microdegree position pairs")
        try:
            start, end = map(point, segment)
        except (ValueError, TypeError):
            raise gl.vm.UserError("Expected two microdegree position pairs")
        if start == end:
            raise gl.vm.UserError("Segment endpoints must differ")

        def evaluate():
            try:
                response = gl.nondet.web.get(BASE + zone, headers=HEADERS)
            except Exception:
                raise gl.vm.UserError("NWS acquisition failed")
            if response.status != 200:
                raise gl.vm.UserError("NWS returned an unsuccessful response")
            try:
                geometry = parse_geometry(response.body, zone)
                return canonical(clip_report(zone, geometry, start, end))
            except (ValueError, TypeError, DecimalException):
                raise gl.vm.UserError("NWS evidence unavailable or unsupported")

        def validate(leader):
            if not isinstance(leader, gl.vm.Return):
                return False
            try:
                return evaluate() == leader.calldata
            except Exception:
                return False

        agreed = gl.vm.run_nondet_unsafe(evaluate, validate)
        clip_id = digest(agreed)
        if clip_id not in self.clips:
            self.clips[clip_id] = agreed
        return clip_id

    @gl.public.view
    def get_clip(self, clip_id: str) -> dict:
        if clip_id not in self.clips:
            raise gl.vm.UserError("Unknown clip")
        return json.loads(self.clips[clip_id])
