import fs from 'node:fs';
import assert from 'node:assert/strict';

const proof = JSON.parse(fs.readFileSync('PROOFS.json', 'utf8'));
const github = 'https://github.com/stoneforger10/zone-segment-clip';
const explorer = 'https://explorer-studio.genlayer.com';
assert(proof.verified && proof.unknown_clip_reverted && proof.source.source_match);
assert.equal(proof.transactions.length, 4);
assert.equal(Object.keys(proof.cases).length, 3);
assert(proof.transactions.every(({receipt}) => receipt.committed && receipt.status === 'FINALIZED' &&
  receipt.execution === 'SUCCESS' && receipt.consensus === 'MAJORITY_AGREE' &&
  receipt.leader_only === false && receipt.agree_votes >= 2));

const deployment = `[StudioNet contract](${explorer}/address/${proof.address})`;
const source = `[Deployed source](${github}/blob/${proof.source_commit}/contracts/ZoneSegmentClip.py)`;
const link = t => `[${t.step}](${explorer}/tx/${t.hash})`;
const lines = proof.transactions.map(t => {
  const report = proof.cases[t.step]?.report;
  const result = report
    ? `${report.runs.map(run => run[2]).join(' → ')}. Interior fraction \`${report.inside_fraction}\`.`
    : 'Deployed source matched the pinned commit.';
  return `| ${link(t)} | ${result} | ${t.receipt.agree_votes} / ${t.receipt.initial_validators} |`;
});

fs.writeFileSync('LIVE_PROOFS.md', `# StudioNet proof matrix

${deployment} · ${source} · [Receipts and exact reports](PROOFS.json)

Deployed source SHA-256 \`${proof.source.sha256}\`.
All four transactions finalized with majority agreement and successful
execution. The proof runner reads the exact report at the ID returned by
each receipt and compares it to the independent [CAZ006 reference](REFERENCE.json).

| Transaction | Verified result | Agree votes / initial validators |
| --- | --- | --- |
${lines.join('\n')}

The unknown report read reverted. The local direct tests also cover interior
holes, corner-only contact, malformed geometry, and validator disagreement.
`);

const notes = `ZoneSegmentClip divides a straight longitude and latitude segment into intervals inside, outside, and along a U.S. National Weather Service forecast zone. Each report records exact rational cut points, interior coverage, and boundary contacts.

The leader and validators independently fetch the zone's GeoJSON, verify the feature identity, and parse the actual polygon rings into integer microdegrees. Each computes the clipping result, including holes and collinear boundaries. Exact agreement on the geometry digest, contacts, runs, and total interior fraction is required before the report is stored.

StudioNet verified three CAZ006 cases against an independent reference: a crossing with five runs, a fully outside segment, and an edge that lies wholly on the boundary. The result describes planar forecast-zone coverage from the observed geometry.`;
assert(notes.length <= 1000);
fs.writeFileSync('SUBMISSION.md', `**Contribution type** Builder → Intelligent Contracts

**Title** ZoneSegmentClip — Forecast Zone Segment Clipping

**Notes / Description**

${notes}

**Evidence**

- [Repository](${github})
- ${source}
- ${deployment}
- [Live proof matrix](${github}/blob/main/LIVE_PROOFS.md)
${proof.transactions.map(t => '- ' + link(t)).join('\n')}
`);
