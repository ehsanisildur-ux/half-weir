# HalfWeir

A standalone GenLayer allocator for a replenished pool that cannot satisfy all declared claims at once. Consensus interprets a frozen public claim record; cumulative funding advances a discrete Talmud-rule allocation. Only newly owed ticks are paid, even if a beneficiary has already transferred earlier payouts.

**Native credits are abstract contract state.** One whole record credit equals two native ticks. These ticks are not GEN, cash, redeemable tokens, legal claims or proof of service delivery. A downstream consumer must actually enforce any entitlement represented by a balance.

The sponsor fixes 2–5 beneficiaries, a source repository/commit URL/hash and a bounded native endowment. Anyone can assess the complete record. Leader and validators independently fetch it, derive every finalized unpaid amount, and audit each amount and source anchor. Proposed reimbursements do not count as paid; withdrawn estimates do not become claims. An unresolved amount is `-1`, never omitted or treated as zero. Any unresolved claimant places the whole pool in REVIEW and blocks funding.

Once claims are resolved, the sponsor funds tranches and anyone distributes them. The contract recomputes entitlement from **total funding to date**, subtracts cumulative awards, and atomically moves only the difference from the pool to beneficiary balances. Transferring a balance does not erase the award history. Unused sponsor credit, escrowed ticks and beneficiary balances always conserve the original native endowment.

- [Contract](contracts/half_weir.py)
- [Design, arithmetic and trust boundary](docs/design.md)
- [Tests](tests/direct/test_weir.py)
- [Onchain proofs](proofs/README.md)
- [Contribution text](docs/submission.md)

## Run locally

```sh
python -m pip install -r requirements-dev.txt
genvm-lint download --version v0.2.16
genvm-lint check contracts/half_weir.py --json
python -m pytest tests/direct -q
node --test tests/rpc-preflight.test.cjs
```

Direct tests explicitly execute validator callbacks with mocked web/model answers. Allocation tests compare binary-search water filling against sorted marginal tickets and an exact Fraction-based continuous reference. The live suite uses real GenVM consensus, public web acquisition, four signing wallets, and full before/after state checks.

## Attribution

The continuous Talmud rule is established work: [Aumann and Maschler, Journal of Economic Theory 36 (1985)](https://gwern.net/doc/statistics/decision/1985-aumann.pdf). HalfWeir implements an integer-tick variant with a documented index tie rule; it does not claim a new bankruptcy theorem or legal prescription. Generic CLI transport, receipt decoding, encrypted CI-account setup and the Windows direct-test workaround are reused under the included MIT license from [PivotBond](https://github.com/mohammadisina1988-jpg/pivot-bond) and earlier repositories. The cumulative allocation protocol, independent tick oracle and tests are implemented here.
