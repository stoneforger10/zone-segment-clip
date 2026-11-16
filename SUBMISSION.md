**Contribution type** Builder → Intelligent Contracts

**Title** ZoneSegmentClip — Forecast Zone Segment Clipping

**Notes / Description**

ZoneSegmentClip divides a straight longitude and latitude segment into intervals inside, outside, and along a U.S. National Weather Service forecast zone. Each report records exact rational cut points, interior coverage, and boundary contacts.

The leader and validators independently fetch the zone's GeoJSON, verify the feature identity, and parse the actual polygon rings into integer microdegrees. Each computes the clipping result, including holes and collinear boundaries. Exact agreement on the geometry digest, contacts, runs, and total interior fraction is required before the report is stored.

StudioNet verified three CAZ006 cases against an independent reference: a crossing with five runs, a fully outside segment, and an edge that lies wholly on the boundary. The result describes planar forecast-zone coverage from the observed geometry.

**Evidence**

- [Repository](https://github.com/stoneforger10/zone-segment-clip)
- [Deployed source](https://github.com/stoneforger10/zone-segment-clip/blob/c50579ac1d813b38b06d1ae32e289a99be34f156/contracts/ZoneSegmentClip.py)
- [StudioNet contract](https://explorer-studio.genlayer.com/address/0x99879b0A9D044c8023584f8323A87CC55301f2E7)
- [Live proof matrix](https://github.com/stoneforger10/zone-segment-clip/blob/main/LIVE_PROOFS.md)
- [deploy](https://explorer-studio.genlayer.com/tx/0x9ed523d32a445f205adfd0dfa58f068a580295c380a22b07e6e375e0c23af290)
- [traverse](https://explorer-studio.genlayer.com/tx/0xb400f7237c529c5b4ecdc467b0bda393ac7bec07cc3e995a540d7fa00dbecd29)
- [outside](https://explorer-studio.genlayer.com/tx/0x06014d0eec4699c932e934916d6b1d9df1658e65af6351407fcfa04e612b6b0f)
- [boundary](https://explorer-studio.genlayer.com/tx/0xde3bb9310b06ff2deb7930dc8f5803501075cbe760e308ea654cd1437142bec4)
