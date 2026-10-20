# Architecture

## Purpose and authority

HalfWeir is a reusable native-credit shortfall allocator: a fixed beneficiary roster shares a scarce replenished pool under an explicit equal-awards/equal-losses policy. Useful consumers include contract-enforced restitution entitlements or educational claim-allocation experiments. Source interpretation determines native entitlements; the economic rule then makes actual balance changes. No certificate or graph transition is issued.

Constructor → fixed full-commit public record → permissionless semantic assessment with independent validators → sponsor-signed funding → permissionless cumulative distribution → beneficiary-signed transfers.

The source author supplies reported claim facts. The sponsor chooses that source once. SHA-256 and the URL bind immutable bytes, not author honesty or offchain legal validity. The contract verifies what the complete record says; it cannot establish that synthetic reimbursements occurred outside the chain. Claimants cannot supply a replacement amount to a write method. There is no mutable source, owner override, deployment upgrade or claimant-ranking command.

## Evidence and consensus

The fetched JSON envelope has exactly `pool`, `claimants` and `clauses`. Pool and complete claimant order must match constructor scope. Duplicate keys, invalid UTF-8, oversized bodies, empty/oversized clauses and extra envelope fields are rejected. The source must be a raw GitHub HTTPS file in the fixed repository, under a full 40-character commit and bounded fixture basename.

The leader interprets every current finalized eligible unpaid amount in whole record credits. Completed reimbursements reduce the same claim. Mere payment proposals, withdrawn estimates, conditional requests and different claimants' balances do not. An explicit no-claim statement can establish zero; silence cannot. Each known amount needs material clause anchors. Unsupported or unresolved amounts cannot be guessed into a payout.

Validators independently fetch the complete source, check the raw-byte hash, reproduce every amount and compare the integer vector exactly. They separately audit every proposed amount, zero and `-1` against all clauses and its anchors. Even an empty unresolved anchor list needs a full-record audit. Verdicts must be actual booleans with no extra fields and all true. No confidence tolerance can cross the funding boundary.

One bounded schema-repair call may correct a malformed model output. It cannot replace missing facts with zero or silently coerce strings/null to amounts. A second malformed output raises an LLM error and validators disagree. Matching external errors may agree on a failed transaction; transient failures may agree only as failures. No failed assessment can fund a beneficiary.

## Discrete allocation

Let whole-credit claims be `c[i]` and total funded native ticks be `E`. One whole record credit is two ticks, so full native claims are `d[i]=2*c[i]`. Half-claim caps `c[i]` are exact integers.

- If `E <= sum(c)`, allocate `CEA(c,E)`.
- Otherwise allocate `d - CEA(c,sum(d)-E)`.

CEA finds the largest integer level L satisfying `sum(min(c[i],L)) <= budget`, then assigns the remaining single ticks to uncapped beneficiaries by constructor index. The implementation uses binary search. Independent tests sort all marginal tickets `(level,index)` instead. A Fraction-based reference checks that each component differs from the continuous rule by less than one native tick.

This discretization conserves every tick and is componentwise monotone in E. It satisfies exact complementary-estate duality with the same tie order. Equal claims can differ by one tick, so index ties are not anonymous. No claim is made that the rounded result inherits every continuous nucleolus or consistency theorem.

## Cumulative payment accounting

Maintain `awarded[i]` separately from current spendable `credits[i]`. At distribution:

`target = allocation(claims, funded_total)`

`delta[i] = target[i] - awarded[i]`

All deltas must be nonnegative and sum to the funded but unpaid pool. Pay delta, update the cumulative award, append the round and empty the pool atomically. Never apply the rule independently to the latest tranche and never compute unpaid entitlement from a beneficiary's current balance. Funding partition changes round history, not total awards at the same cumulative estate.

For claims `[2,4,6]` whole credits, full claims are `[4,8,12]` ticks. At funded totals 6, 12, 18 and 24 ticks the targets are respectively `[2,2,2]`, `[2,4,6]`, `[2,6,10]` and `[4,8,12]`. The half-estate boundary is 12 ticks. If Aster transfers one tick after the first payout, Aster still has a cumulative award of two; the next round owes Aster zero, not one.

After every funding, distribution and transfer:

`sponsor_balance + pool_balance + sum(credits) == initial_endowment`

`sum(credits) == sum(awarded)`

`funded_total == pool_balance + sum(awarded) == sum(fundings)`

Transfers circulate native ticks only among the fixed beneficiaries. They never alter claims, cumulative funding or cumulative awards. The sponsor cannot transfer a beneficiary's balance. Assessment and distribution are deliberately permissionless; funding is sponsor-only and spending is beneficiary-only.

## States and bounds

UNASSESSED becomes REVIEW if any amount is unresolved; otherwise ACTIVE, or SATISFIED when all claims are zero. REVIEW cannot accept funding. A full distribution becomes SATISFIED when all full native claims are paid, or EXHAUSTED when the sponsor's endowment is spent first. Beneficiaries can still transfer already paid balances in either terminal state.

Bounds: 2–5 unique beneficiary wallets and labels, sponsor distinct from all beneficiaries, 0–1000 whole credits per known claim, 1–10,000 endowed native ticks, at most 32 funding tranches and 64 transfers. Funding cannot exceed the sponsor balance or total full claims. Multiple funds may accumulate before a distribution; hitting the tranche limit does not prevent distributing an already funded pool. There are no fees, floating-point calculations, external token calls, generated code or cross-contract messages.

The sponsor can withhold future tranches. Source/model/network availability or substantive disagreement can block assessment; no pre-assessment funding is accepted. Endowments are synthetic internal state with no GEN withdrawal or promised external redemption. Tests and examples do not establish the factual or legal truth of a claim record.

## Distinctness

EndowSwap exchanges indivisible endowed rights through trading cycles. PivotBond uses counterfactual welfare prices for bundle-valued bidding. TrancheWeave vests a grant over time. HalfWeir instead freezes a semantic net-claim vector and advances a two-regime, cumulative shortfall allocation across funding tranches. Its separate award and spendable ledgers prevent payouts transferred away from being paid again. There is no auction, self-reported agent trace, versioned graph proposal, service certificate or one-time certificate consumption.
