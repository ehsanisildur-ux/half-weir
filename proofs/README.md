# StudioNet scenario proofs

Live deployment and scenario receipts are pending. A deployment alone will not count as a passing payout pool.

| Scenario | Required effect |
| --- | --- |
| staircase | Four cumulative payouts cross the awards/losses boundary. A beneficiary transfers before top-up; later rounds pay only newly owed amounts. Unauthorized funding and repeated empty distribution are rejected. |
| lopsided | Small claims cap early; integer remainder ties and full satisfaction are checked. Overfunding is rejected. |
| review | An unresolved claimant stays in the vector. The complete pool remains REVIEW; funding and payout attempts are rejected with unchanged balances. |

Each signed call is checked against a separate per-tick oracle and its complete before/after state. Final verification re-fetches exact deployed source, complete final votes, actual signers and calldata, expected-error bytes and the full live ledger. All credit amounts are synthetic native ticks, not GEN or evidence that services were delivered.
