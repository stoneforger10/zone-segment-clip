# StudioNet proof matrix

[StudioNet contract](https://explorer-studio.genlayer.com/address/0x99879b0A9D044c8023584f8323A87CC55301f2E7) · [Deployed source](https://github.com/stoneforger10/zone-segment-clip/blob/c50579ac1d813b38b06d1ae32e289a99be34f156/contracts/ZoneSegmentClip.py) · [Receipts and exact reports](PROOFS.json)

Deployed source SHA-256 `11f0ef50719a767d9347229cae7d6a430635bd735b482da7442ba8608f0476ae`.
All four transactions finalized with majority agreement and successful
execution. The proof runner reads the exact report at the ID returned by
each receipt and compares it to the independent [CAZ006 reference](REFERENCE.json).

| Transaction | Verified result | Agree votes / initial validators |
| --- | --- | --- |
| [deploy](https://explorer-studio.genlayer.com/tx/0x9ed523d32a445f205adfd0dfa58f068a580295c380a22b07e6e375e0c23af290) | Deployed source matched the pinned commit. | 3 / 5 |
| [traverse](https://explorer-studio.genlayer.com/tx/0xb400f7237c529c5b4ecdc467b0bda393ac7bec07cc3e995a540d7fa00dbecd29) | outside → inside → outside → inside → outside. Interior fraction `1231265731/19225200000`. | 3 / 5 |
| [outside](https://explorer-studio.genlayer.com/tx/0x06014d0eec4699c932e934916d6b1d9df1658e65af6351407fcfa04e612b6b0f) | outside. Interior fraction `0/1`. | 3 / 5 |
| [boundary](https://explorer-studio.genlayer.com/tx/0xde3bb9310b06ff2deb7930dc8f5803501075cbe760e308ea654cd1437142bec4) | boundary. Interior fraction `0/1`. | 3 / 5 |

The unknown report read reverted. The local direct tests also cover interior
holes, corner-only contact, malformed geometry, and validator disagreement.
