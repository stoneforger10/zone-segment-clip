# ZoneSegmentClip

ZoneSegmentClip splits a straight longitude and latitude segment into
intervals inside, outside, and along a U.S. National Weather Service forecast
zone. This is useful for annotating segments with forecast coverage.

Call `clip(zone, [[longitude, latitude], [longitude, latitude]])` with signed
integer microdegrees. The leader and every validator independently fetch the
zone's GeoJSON. They verify the feature identity and parse the polygon rings
into integer coordinates. Each computes exact rational intersections,
classifies the intervals including holes and collinear edges, and agrees on
the entire canonical report. Empty, malformed, or unsupported geometry
stops the write.

`get_clip(id)` returns the content-addressed result. The report binds the
segment and normalized geometry digest to the ordered runs, the exact
boundary contacts, and the total fraction in the interior. Runs describe
open intervals. A single tangency appears in the contacts even when the
same outside run passes through it. Boundary overlap is a separate run
and contributes zero to the interior fraction.

The contract works on continental coordinates and accepts 2D Polygon or
MultiPolygon shapes of up to 6,000 vertices and up to 64 contacts per query.
It uses the source's ring topology and six-decimal coordinates. The result
describes a planar line in longitude and latitude using the observed zone
geometry. Weather and route conditions require separate observations.

[NWS forecast zones](https://www.weather.gov/gis/publiczones) ·
[NWS API](https://www.weather.gov/documentation/services-web-api) ·
[GeoJSON specification](https://www.rfc-editor.org/rfc/rfc7946.html)

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
genvm-lint check contracts/ZoneSegmentClip.py
```

`REFERENCE.json` records the proof vectors derived from the public
[CAZ006 feature](https://api.weather.gov/zones/forecast/CAZ006). To regenerate
them, download that GeoJSON and run `python scripts/reference.py <file>`.
The independent reference uses a horizontal scanline for the traversal
cases. The proof runner uses the pinned JS SDK (`npm ci`) and records writes
before polling. Its `--verify-only` flag verifies existing receipts and reads.
