Category: Builder → Intelligent Contracts

Title: HalfWeir: Consensus cumulative shortfall allocation

Notes / Description:

> HalfWeir allocates a replenished native-credit pool against independently interpreted claims. Leader and validators fetch a commit-pinned record, derive each finalized unpaid amount and audit corrections, reimbursements and source anchors. Exact amount/unresolved agreement blocks funding if any claimant remains unresolved. Sponsor-signed tranches advance a discrete Talmud allocation; permissionless distribution pays only new cumulative entitlement. Separate award and spendable ledgers prevent transferred payouts being paid again. Integer water filling crosses equal-awards/equal-losses regimes. Three StudioNet pools show four top-ups, a transfer before later payouts, capped small claims and an unresolved pool. All 26 finalized MAJORITY_AGREE receipts match fresh state, including five expected rejections. Tests cover 1,625 exhaustive estates and 96 generated five-claimant cases; 76 direct tests and seven transport tests pass. Native ticks are synthetic, not GEN or legal claims.

Evidence:

- [Public repository](https://github.com/ehsanisildur-ux/half-weir)
- [GenLayer contract source](https://github.com/ehsanisildur-ux/half-weir/blob/main/contracts/half_weir.py)
- [Primary GenLayer contract explorer](https://explorer-studio.genlayer.com/address/0xe83355E4E5D7645f2FDBcE2e05AF641453245961)
- [Onchain scenario proofs](https://github.com/ehsanisildur-ux/half-weir/blob/main/proofs/README.md)
- [Deployment transaction](https://explorer-studio.genlayer.com/tx/0xbc2254af29cc4729444e22eca5cf81438ecc52c8c5d59c6d096c9bb7a8c5201a)
- [Passing CI](https://github.com/ehsanisildur-ux/half-weir/actions/runs/39488080426)
