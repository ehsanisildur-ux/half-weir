# StudioNet scenario proofs

**26 verified primary receipts: 21 successful executions and five expected execution errors.** Every receipt is FINALIZED with MAJORITY_AGREE on gasless StudioNet, chain 61999. [verification.json](verification.json) records `scope: all`, complete calldata/signature checks and `live_state_match: true` from independent fresh RPC/state verification.

Exact source SHA-256: `a55fcd466bcfc2a4dd5e28963591f8e16a19bc15b209abd3a5076666c83d9f45`. [Deployed source at revision 5928dfe](https://github.com/ehsanisildur-ux/half-weir/blob/5928dfe31ab859e7ff1b2fe17546daf8ee711c58/contracts/half_weir.py). Source/test revision: `5928dfe31ab859e7ff1b2fe17546daf8ee711c58`. Public fixture revision: `8376c6b5046439781cbfbf4ff1a1655aaaa85fcb`.

| Scenario | Contract explorer | Receipts | Verified final effect |
| --- | --- | --- | --- |
| staircase | [0xe833…5961](https://explorer-studio.genlayer.com/address/0xe83355E4E5D7645f2FDBcE2e05AF641453245961) | 13 | Claims `[2,4,6]` whole credits; cumulative awards `[4,8,12]` ticks. A transfer before later funding leaves spendable balances `[3,9,12]`, without a repeated payout. Phase SATISFIED. |
| lopsided | [0x8970…29d9](https://explorer-studio.genlayer.com/address/0x89704E3a23328fEF265bCeB31fAcc976551e29d9) | 9 | Claims `[1,3,7]` whole credits; final awards and balances `[2,6,14]` ticks. Small claims cap early; overfunding is rejected. Phase SATISFIED. |
| review | [0x20C5…f549](https://explorer-studio.genlayer.com/address/0x20C53f515445d16b9Ba40484B5e838e3a557f549) | 4 | Claims `[2,-1,6]` preserve the unresolved claimant. Sponsor retains 24 ticks, funding stays zero and beneficiary balances stay zero. Funding and payout attempts fail. Phase REVIEW. |

Every final funded-but-unpaid pool is zero. Amounts below are native ticks; one whole record credit is two ticks. They are synthetic internal endowments, not GEN, external reimbursements or verified legal claims.

## Cumulative payouts

| Pool | Cumulative funded ticks | Regime | Cumulative awards | Newly paid delta |
| --- | --- | --- | --- | --- |
| staircase | 6 | AWARDS | `[2,2,2]` | `[2,2,2]` |
| staircase | 12 | AWARDS | `[2,4,6]` | `[0,2,4]` |
| staircase | 18 | LOSSES | `[2,6,10]` | `[0,2,4]` |
| staircase | 24 | LOSSES | `[4,8,12]` | `[2,2,2]` |
| lopsided | 5 | AWARDS | `[1,2,2]` | `[1,2,2]` |
| lopsided | 16 | LOSSES | `[1,3,12]` | `[0,1,10]` |
| lopsided | 22 | LOSSES | `[2,6,14]` | `[1,3,2]` |

After the first staircase distribution, beneficiary 0 transferred one tick to beneficiary 1. At the 12-tick and 18-tick distributions, beneficiary 0 still received zero new ticks. The ledger uses cumulative awards rather than spendable balances to calculate what remains owed.

## Decisive transactions

| Proof | Explorer transaction |
| --- | --- |
| Primary deployment | [deploy](https://explorer-studio.genlayer.com/tx/0xbc2254af29cc4729444e22eca5cf81438ecc52c8c5d59c6d096c9bb7a8c5201a) |
| Current net claims from corrected/reimbursed source clauses | [assess](https://explorer-studio.genlayer.com/tx/0x07ca5e9dd8005566b1fce2f208d8402e19a603c05f9d3d50d02fb815dd630b6c) |
| First cumulative distribution | [6 ticks](https://explorer-studio.genlayer.com/tx/0xe44c0d3b906d1f89e04c4144d7cbd7a7ec84003281e4d868dffe4700c51237da) |
| Beneficiary transfer before the next top-up | [transfer](https://explorer-studio.genlayer.com/tx/0x072b47740cf1aa934a2887b30b27d7f1247dbc38b174d1e25c72f47b5346e415) |
| Half-estate boundary, without repaying spent credit | [12 ticks](https://explorer-studio.genlayer.com/tx/0xbaa4703ccbfa779a44ffebf89722eca43ab27049e79f213a42cbe629d4731b92) |
| Equal-losses regime | [18 ticks](https://explorer-studio.genlayer.com/tx/0xdaa8ca39030e172ac383628a90379041c784c2716b455c22891e5bdd555e9936) |
| Full native claim satisfaction | [24 ticks](https://explorer-studio.genlayer.com/tx/0x75dae98e3b5b64034c1398b452c7abb518a0ed31fb666d7309fa6cd7dfeeb4a7) |
| Non-sponsor funding rejection | [expected error](https://explorer-studio.genlayer.com/tx/0xd4bd446ed6646d0accbd402b3292561ddcce9e81a01d6bf5ae2aaedc5cbfa2c8) |
| Empty repeated distribution rejection | [expected error](https://explorer-studio.genlayer.com/tx/0x1f9fdf93e5b75783fbe2d9ac6a4f0133666861dbef933756d0fe639d6dc1180c) |
| Capped-claims deployment | [deploy](https://explorer-studio.genlayer.com/tx/0x7eac7ee01e02774dd432d3fd206f8880afb531a88130022cf9d4362ba967b8bd) |
| Early small-claim cap | [5 ticks](https://explorer-studio.genlayer.com/tx/0xc463be00a520a127ec720a1c0ce3bccdb0eb9c60222c3b1b727bd165b5b5c772) |
| Discrete losses and remainder tie | [16 ticks](https://explorer-studio.genlayer.com/tx/0x34ea9ad2e93cc12f3a989bd1a2d01c816304a6a562c9b744f6aee6b5ce0cf050) |
| Overfunding rejection | [expected error](https://explorer-studio.genlayer.com/tx/0xfd05fcad37d5be6b5104d98003e158140d2e268affe17f1af4c8e7af93cc2447) |
| Capped-claims full satisfaction | [22 ticks](https://explorer-studio.genlayer.com/tx/0xb9ba7be6af62f8687f451133d072066940f85ef05cbae17a839bb5951bb1823a) |
| Unresolved-claim deployment | [deploy](https://explorer-studio.genlayer.com/tx/0xee76a696217f9b95d136dea8e8c76198afa1c43d9c54962a29c4e8ea6eaccabe) |
| Independently agreed unresolved amount | [assess](https://explorer-studio.genlayer.com/tx/0x735bcbf954b4351c70d1bfc273e32daf27a8d93a380b10131554273fe19b6599) |
| REVIEW blocks sponsor funding | [expected error](https://explorer-studio.genlayer.com/tx/0x3f5e7c75fd249e85129b3ed2bc2b6e9c9e947de267ad3ff54d484d3cdb83cde7) |
| REVIEW blocks distribution | [expected error](https://explorer-studio.genlayer.com/tx/0x8f4f6e8e05e30cc6b65c2895d7c5d2507032efbae895ed74931c5ef97a8c611b) |

Each signed call is checked against a separate per-tick oracle and its complete before/after state. Final verification re-fetches exact deployed source, complete final votes, actual signers and calldata, expected-error bytes and the full live ledger. All credit amounts are synthetic native ticks, not GEN or evidence that services were delivered.

## Machine evidence and provenance

[transactions.json](transactions.json) lists all 26 hashes. [suite.json](suite.json) binds constructor arguments, source hashes and four distinct signing accounts per instance. The `*-trace.json` files retain every complete state before and after a call; `*-receipt.json` files retain execution results, decoded-call binding data and complete final votes. Expected errors are checked byte-for-byte with unchanged state. [provenance.json](provenance.json) records workflow origins.

Final vote distributions `(agree/disagree/idle)` are `5/0/0` for 14 receipts, `3/0/2` for 10, `4/0/1` for 1, and `3/1/1` for 1. The REVIEW assessment preserves one dissent and one idle vote. Majority agreement is not a unanimity claim.

- [Staircase workflow](https://github.com/ehsanisildur-ux/half-weir/actions/runs/39488078755)
- [Capped-claims workflow](https://github.com/ehsanisildur-ux/half-weir/actions/runs/39488084973)
- [Unresolved-claim workflow](https://github.com/ehsanisildur-ux/half-weir/actions/runs/39488092353)
- [Passing CI](https://github.com/ehsanisildur-ux/half-weir/actions/runs/39488080426)

All three hosted JUnit reports and the local report contain 76 direct tests, zero failures/errors/skips. Seven transport tests verify bounded read-only retries and that signed sends are never replayed after ambiguous failures. Direct tests mock models/web but explicitly invoke validator callbacks. Live receipts use actual acquisition and GenVM consensus. The 1,625 exhaustive estates and 96 generated five-claimant cases are local property coverage; they are not additional onchain transactions.

## Reproduce

With GenLayer CLI `0.39.2` installed, set `GENLAYER_CLI_PATH` to its absolute `dist/index.js` path. Run `node scripts/verify-proofs.cjs --offline` to verify saved receipts and traces. Set `WEIR_ACCOUNT` to a configured read account and run `node scripts/verify-proofs.cjs` for fresh RPC/source/state verification. Neither verifier sends transactions. The manual StudioNet workflow deploys fresh pools with encrypted disposable signing wallets.
