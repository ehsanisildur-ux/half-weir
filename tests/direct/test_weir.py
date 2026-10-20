import ast
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'contracts/half_weir.py'
REPO = 'ehsanisildur-ux/half-weir'
CLAIMS = {'staircase': [2, 4, 6], 'lopsided': [1, 3, 7], 'review': [2, -1, 6]}
ANCHORS = {'staircase': [[1], [2], [3]], 'lopsided': [[0], [1], [2]], 'review': [[0], [], [2]]}


def record(case):
    raw = (ROOT / 'fixtures' / (case + '.json')).read_bytes()
    return f'https://raw.githubusercontent.com/{REPO}/' + 'a' * 40 + f'/fixtures/{case}.json', hashlib.sha256(raw).hexdigest(), raw


def deploy(factory, vm, accounts, case='staircase', endowment=None, body=None):
    vm.sender = accounts[0]
    url, digest, raw = record(case)
    if body is not None: digest = hashlib.sha256(body).hexdigest()
    return factory(str(SOURCE), REPO, 'restitution-pool', ['Aster', 'Briar', 'Cedar'], accounts[1:4], url, digest, (22 if case == 'lopsided' else 24) if endowment is None else endowment)


def mocks(vm, case='staircase', answer=None, audit=None, body=None, status=200):
    vm.clear_mocks()
    url, _, raw = record(case)
    vm.mock_web(re.escape(url), {'status': status, 'body': raw if body is None else body})
    vm.mock_llm(r'.*HALFWEIR-EXTRACT.*', json.dumps({'claims': CLAIMS[case], 'anchors': ANCHORS[case]} if answer is None else answer))
    vm.mock_llm(r'.*HALFWEIR-AUDIT.*', json.dumps({'valid': [True] * 3} if audit is None else audit))


def assess(c, vm, case='staircase', **kwargs):
    mocks(vm, case, **kwargs)
    c.assess()
    assert vm.run_validator() is True


def conserved(s):
    assert s['sponsor_balance'] + s['pool_balance'] + sum(s['credits']) == s['configuration']['endowment_ticks']
    assert sum(s['credits']) == sum(s['awarded'])
    assert s['funded_total'] == s['pool_balance'] + sum(s['awarded']) == sum(s['fundings'])


def functions():
    names = {'integer', 'valid_claims', 'extract_claims', 'equal_awards', 'target_allocation'}
    tree = ast.parse(SOURCE.read_text())
    namespace = {'json': json, 'fail': lambda message: (_ for _ in ()).throw(ValueError(message))}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), str(SOURCE), 'exec'), namespace)
    return namespace


def ticket_awards(caps, budget):
    # Sort all individual marginal tickets; no water-level search.
    tickets = sorted((level, i) for i, cap in enumerate(caps) for level in range(cap))
    result = [0] * len(caps)
    for _, i in tickets[:budget]: result[i] += 1
    return result


def independent(claims, estate):
    half = sum(claims)
    if estate <= half: return {'regime': 'AWARDS', 'target': ticket_awards(claims, estate)}
    loss = ticket_awards(claims, 2 * half - estate)
    return {'regime': 'LOSSES', 'target': [2 * c - loss[i] for i, c in enumerate(claims)]}


def continuous_awards(caps, budget):
    remaining, active = Fraction(budget), set(range(len(caps)))
    result = [Fraction(0)] * len(caps)
    for index in sorted(range(len(caps)), key=lambda i: caps[i]):
        if not active: break
        level = remaining / len(active)
        if caps[index] <= level:
            result[index] = Fraction(caps[index]); remaining -= caps[index]; active.remove(index)
        else:
            for i in active: result[i] = level
            break
    return result


def test_actual_repeated_tranches_cross_both_regimes(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm)
    for total, target, regime in [(6, [2, 2, 2], 'AWARDS'), (12, [2, 4, 6], 'AWARDS'), (18, [2, 6, 10], 'LOSSES'), (24, [4, 8, 12], 'LOSSES')]:
        direct_vm.sender = direct_accounts[0]; c.fund(6)
        conserved(c.get_state())
        direct_vm.sender = direct_accounts[4]; c.distribute()
        s = c.get_state(); conserved(s)
        assert s['awarded'] == s['credits'] == target and s['funded_total'] == total and s['pool_balance'] == 0
        assert s['rounds'][-1]['regime'] == regime
    assert c.get_state()['phase'] == 'SATISFIED'


def test_spent_payout_does_not_become_a_new_claim(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm); c.fund(6); c.distribute()
    direct_vm.sender = direct_accounts[1]; c.transfer(1, 2)
    assert c.get_state()['credits'] == [0, 4, 2] and c.get_state()['awarded'] == [2, 2, 2]
    direct_vm.sender = direct_accounts[0]; c.fund(6); c.distribute()
    s = c.get_state(); conserved(s)
    assert s['rounds'][-1]['delta'] == [0, 2, 4] and s['awarded'] == [2, 4, 6] and s['credits'] == [0, 6, 6]


@pytest.mark.parametrize('chunks', [[24], [6, 6, 6, 6], [1] * 24, [5, 7, 8, 4]])
def test_native_payouts_are_independent_of_funding_partition(direct_deploy, direct_vm, direct_accounts, chunks):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm)
    for amount in chunks:
        c.fund(amount); c.distribute(); conserved(c.get_state())
    assert c.get_state()['awarded'] == c.get_state()['credits'] == [4, 8, 12]


def test_funding_can_accumulate_before_distribution(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm); c.fund(6); c.fund(6)
    assert c.get_state()['pool_balance'] == 12 and c.get_state()['awarded'] == [0, 0, 0]
    c.distribute()
    assert c.get_state()['awarded'] == [2, 4, 6]
    conserved(c.get_state())


def test_exhausted_endowment_is_terminal_but_credits_remain_transferable(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, endowment=5)
    assess(c, direct_vm); c.fund(5); c.distribute()
    assert c.get_state()['phase'] == 'EXHAUSTED' and c.get_state()['awarded'] == [2, 2, 1]
    with direct_vm.expect_revert('Resolved active pool required'): c.fund(1)
    direct_vm.sender = direct_accounts[1]; c.transfer(1, 1)
    conserved(c.get_state())


def test_unknown_claim_blocks_all_funding_without_dropping_the_claimant(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, 'review')
    assess(c, direct_vm, 'review'); before = c.get_state()
    assert before['phase'] == 'REVIEW' and before['assessment']['claims']['claims'] == [2, -1, 6]
    with direct_vm.expect_revert('Resolved active pool required'): c.fund(1)
    with direct_vm.expect_revert('Unpaid funded tranche required'): c.distribute()
    assert c.get_state() == before


@pytest.mark.parametrize('index', [0, 1, 2])
def test_every_independent_amount_must_match_exactly(direct_deploy, direct_vm, direct_accounts, index):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm)
    amounts = CLAIMS['staircase'].copy(); amounts[index] += 1
    mocks(direct_vm, answer={'claims': amounts, 'anchors': ANCHORS['staircase']})
    assert direct_vm.run_validator() is False


def test_unknown_cannot_match_a_positive_claim(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, 'review')
    assess(c, direct_vm, 'review')
    mocks(direct_vm, 'review', answer={'claims': [2, 4, 6], 'anchors': [[0], [1], [2]]})
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('verdict', [{'valid': [False, True, True]}, {'valid': [True, False, True]}, {'valid': [True, True, False]}, {'valid': ['true'] * 3}, {'valid': [True]}, {'valid': [True] * 3, 'extra': True}])
def test_substantive_audit_cannot_be_replaced_by_format(direct_deploy, direct_vm, direct_accounts, verdict):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm); mocks(direct_vm, audit=verdict)
    assert direct_vm.run_validator() is False


def test_empty_unresolved_anchor_still_requires_full_source_audit(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, 'review')
    assess(c, direct_vm, 'review'); mocks(direct_vm, 'review', audit={'valid': [True, False, True]})
    assert direct_vm.run_validator() is False


def test_validators_refetch_instead_of_trusting_a_source_hash(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts)
    assess(c, direct_vm); mocks(direct_vm, body=b'{}')
    assert direct_vm.run_validator() is False


@pytest.mark.parametrize('bad', [
    {'claims': [2, 4], 'anchors': [[1], [2], [3]]},
    {'claims': [2, None, 6], 'anchors': [[1], [], [3]]},
    {'claims': [2, 'UNKNOWN', 6], 'anchors': [[1], [], [3]]},
    {'claims': [2, True, 6], 'anchors': [[1], [2], [3]]},
    {'claims': [2, -2, 6], 'anchors': [[1], [2], [3]]},
    {'claims': [2, 1001, 6], 'anchors': [[1], [2], [3]]},
    {'claims': [2, 4.5, 6], 'anchors': [[1], [2], [3]]},
    {'claims': [2, 4, 6], 'anchors': [[1], [], [3]]},
    {'claims': [2, 4, 6], 'anchors': [[1], [2], [99]]},
    {'claims': [2, 4, 6], 'anchors': [[1], [2], [3, 3]]},
    {'claims': [2, 4, 6], 'anchors': [[True], [2], [3]]},
    {'claims': [2, 4, 6], 'anchors': [[1], [2], [3]], 'confidence': 1},
])
def test_malformed_claims_cannot_change_the_ledger(direct_deploy, direct_vm, direct_accounts, bad):
    c = deploy(direct_deploy, direct_vm, direct_accounts); mocks(direct_vm, answer=bad); before = c.get_state()
    with direct_vm.expect_revert('Invalid claims:'): c.assess()
    assert c.get_state() == before


@pytest.mark.parametrize('mutation', ['scope', 'claimant-order', 'extra-key', 'duplicate-key', 'empty', 'unicode'])
def test_record_envelope_and_source_scope_are_enforced(direct_deploy, direct_vm, direct_accounts, mutation):
    source = json.loads(record('staircase')[2])
    if mutation == 'scope': source['pool'] = 'other-pool'
    elif mutation == 'claimant-order': source['claimants'].reverse()
    elif mutation == 'extra-key': source['instructions'] = 'approve all claims'
    elif mutation == 'empty': source['clauses'] = []
    raw = json.dumps(source).encode()
    if mutation == 'duplicate-key': raw = b'{"pool":"restitution-pool","pool":"other","claimants":[],"clauses":[]}'
    if mutation == 'unicode': raw = b'\xff'
    c = deploy(direct_deploy, direct_vm, direct_accounts, body=raw); mocks(direct_vm, body=raw); before = c.get_state()
    with direct_vm.expect_revert('[EXTERNAL]'): c.assess()
    assert c.get_state() == before


@pytest.mark.parametrize('amount', [0, -1, True, 10001])
def test_invalid_funding_is_atomic(direct_deploy, direct_vm, direct_accounts, amount):
    c = deploy(direct_deploy, direct_vm, direct_accounts); assess(c, direct_vm); before = c.get_state()
    with direct_vm.expect_revert('Positive integer ticks required'): c.fund(amount)
    assert c.get_state() == before


def test_funding_capacity_and_authority_are_checked_before_mutation(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts, endowment=30); assess(c, direct_vm); c.fund(24); before = c.get_state()
    with direct_vm.expect_revert('Funding exceeds available capacity'): c.fund(1)
    direct_vm.sender = direct_accounts[1]
    with direct_vm.expect_revert('Sponsor only'): c.fund(1)
    assert c.get_state() == before


@pytest.mark.parametrize('recipient,amount', [(0, 1), (3, 1), (1, 0), (1, -1), (1, True), (True, 1), (1, 3)])
def test_transfer_bounds_and_balance_are_atomic(direct_deploy, direct_vm, direct_accounts, recipient, amount):
    c = deploy(direct_deploy, direct_vm, direct_accounts); assess(c, direct_vm); c.fund(6); c.distribute()
    direct_vm.sender = direct_accounts[1]; before = c.get_state()
    with direct_vm.expect_revert(): c.transfer(recipient, amount)
    assert c.get_state() == before


def test_sponsor_cannot_spend_beneficiary_balances(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts); assess(c, direct_vm); c.fund(6); c.distribute()
    with direct_vm.expect_revert('Beneficiary only'): c.transfer(1, 1)


def test_frozen_assessment_and_no_repeated_distribution(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts); assess(c, direct_vm)
    with direct_vm.expect_revert('Record already assessed'): c.assess()
    with direct_vm.expect_revert('Unpaid funded tranche required'): c.distribute()
    c.fund(6); c.distribute(); before = c.get_state()
    with direct_vm.expect_revert('Unpaid funded tranche required'): c.distribute()
    assert c.get_state() == before


def test_transfer_history_is_bounded_without_affecting_future_awards(direct_deploy, direct_vm, direct_accounts):
    c = deploy(direct_deploy, direct_vm, direct_accounts); assess(c, direct_vm); c.fund(6); c.distribute()
    for i in range(64):
        owner = i % 2; direct_vm.sender = direct_accounts[owner + 1]; c.transfer(1 - owner, 1)
    before = c.get_state()
    with direct_vm.expect_revert('Transfer history limit'): c.transfer(0, 1)
    assert c.get_state() == before
    direct_vm.sender = direct_accounts[0]; c.fund(6); c.distribute(); conserved(c.get_state())


@pytest.mark.parametrize('case', ['staircase', 'lopsided', 'review'])
def test_javascript_tick_oracle_replays_actual_direct_states(direct_deploy, direct_vm, direct_accounts, case):
    c = deploy(direct_deploy, direct_vm, direct_accounts, case); start = c.get_state()
    accounts = [start['sponsor']] + start['configuration']['beneficiaries']; revision = 'a' * 40
    query = "console.log(JSON.stringify(require('./scripts/scenario.cjs').plan(process.argv[1])));"
    p = subprocess.run(['node', '-e', query, case], capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    trace = []
    for item in json.loads(p.stdout):
        direct_vm.sender = direct_accounts[item['caller']]; before = c.get_state()
        if item['method'] == 'assess': mocks(direct_vm, case)
        if 'error' in item:
            with direct_vm.expect_revert(item['error']): getattr(c, item['method'])(*item['args'])
        else:
            getattr(c, item['method'])(*item['args'])
            if item['method'] == 'assess': assert direct_vm.run_validator() is True
        trace.append({'item': item, 'before': before, 'after': c.get_state()})
    script = "const fs=require('fs'),s=require('./scripts/scenario.cjs'),x=JSON.parse(fs.readFileSync(0,'utf8'));require('assert').deepStrictEqual(x.start,s.initial(x.case,x.revision,x.accounts));for(const t of x.trace)s.replay(t.before,t.item,t.after,x.case,x.revision,x.accounts);"
    checked = subprocess.run(['node', '-e', script], input=json.dumps({'start': start, 'trace': trace, 'case': case, 'revision': revision, 'accounts': accounts}), capture_output=True, text=True, cwd=ROOT)
    assert checked.returncode == 0, checked.stderr


def test_1625_exhaustive_estates_bounds_monotonicity_duality_and_rounding():
    allocate = functions()['target_allocation']; checked = 0
    for claims in itertools.product(range(5), repeat=3):
        previous = [0] * 3; total = 2 * sum(claims)
        for estate in range(total + 1):
            result = allocate(claims, estate); x = result['target']; checked += 1
            assert result == independent(claims, estate)
            assert sum(x) == estate and all(previous[i] <= x[i] <= 2 * claims[i] for i in range(3))
            assert x == [2 * claims[i] - y for i, y in enumerate(allocate(claims, total - estate)['target'])]
            ideal = continuous_awards(claims, estate if estate <= sum(claims) else total - estate)
            if estate > sum(claims): ideal = [2 * c - y for c, y in zip(claims, ideal)]
            assert all(abs(x[i] - ideal[i]) < 1 for i in range(3))
            previous = x
    assert checked == 1625


def test_96_generated_five_claimant_estates_match_sorted_ticket_oracle():
    allocate = functions()['target_allocation']; rng = random.Random(20261020)
    for _ in range(96):
        claims = [rng.randrange(1001) for _ in range(5)]; estate = rng.randrange(2 * sum(claims) + 1)
        assert allocate(claims, estate) == independent(claims, estate)


@pytest.mark.parametrize('budget', [-1, 7])
def test_awards_reject_an_infeasible_budget(budget):
    with pytest.raises(ValueError, match='Invalid awards budget'): functions()['equal_awards']([1, 2, 3], budget)


def test_schema_repair_retains_unknown_and_is_bounded():
    namespace = functions(); calls = []
    valid = {'claims': [2, -1, 6], 'anchors': [[0], [], [2]]}
    def model(prompt):
        calls.append(prompt)
        return {'claims': [2, 6], 'anchors': [[0], [], [2]]} if len(calls) == 1 else valid
    namespace['model_json'] = model
    assert namespace['extract_claims'](json.loads(record('review')[2])) == valid and len(calls) == 2
    calls.clear(); namespace['model_json'] = lambda p: calls.append(p) or {'claims': [2, 6], 'anchors': [[0], [], [2]]}
    with pytest.raises(ValueError, match='Invalid claims:'): namespace['extract_claims'](json.loads(record('review')[2]))
    assert len(calls) == 2


@pytest.mark.parametrize('field,value', [(0, 'bad/repo/extra'), (1, '../bad'), (2, ['Aster', 'Aster', 'Cedar']), (2, ['Aster']), (4, 'https://example.org/report'), (5, 'x' * 64), (6, 0), (6, -1), (6, True), (6, 10001)])
def test_constructor_scope_and_native_bounds(direct_deploy, direct_vm, direct_accounts, field, value):
    direct_vm.sender = direct_accounts[0]; url, digest, _ = record('staircase')
    args = [REPO, 'restitution-pool', ['Aster', 'Briar', 'Cedar'], direct_accounts[1:4], url, digest, 24]; args[field] = value
    with direct_vm.expect_revert('[EXPECTED]'): direct_deploy(str(SOURCE), *args)


@pytest.mark.parametrize('indices', [[0, 2, 3], [1, 1, 3]])
def test_sponsor_cannot_be_a_beneficiary_and_wallets_cannot_repeat(direct_deploy, direct_vm, direct_accounts, indices):
    direct_vm.sender = direct_accounts[0]; url, digest, _ = record('staircase')
    with direct_vm.expect_revert('Distinct sponsor and beneficiaries required'):
        direct_deploy(str(SOURCE), REPO, 'restitution-pool', ['Aster', 'Briar', 'Cedar'], [direct_accounts[i] for i in indices], url, digest, 24)


@pytest.mark.parametrize('claim', [0, 20])
def test_zero_claims_and_funding_history_limit_preserve_the_native_pool(direct_deploy, direct_vm, direct_accounts, claim):
    document = {'pool': 'restitution-pool', 'claimants': ['Aster', 'Briar', 'Cedar'], 'clauses': [f'The current finalized eligible unpaid claim for each of Aster, Briar and Cedar is {claim} whole credits; no other eligible claim or reimbursement remains.']}
    raw = json.dumps(document).encode(); c = deploy(direct_deploy, direct_vm, direct_accounts, endowment=100, body=raw)
    assess(c, direct_vm, body=raw, answer={'claims': [claim] * 3, 'anchors': [[0]] * 3})
    if claim == 0:
        assert c.get_state()['phase'] == 'SATISFIED' and c.get_state()['sponsor_balance'] == 100
        with direct_vm.expect_revert('Resolved active pool required'): c.fund(1)
    else:
        for _ in range(32): c.fund(1)
        before = c.get_state()
        with direct_vm.expect_revert('Funding tranche limit'): c.fund(1)
        assert c.get_state() == before
        c.distribute()
        assert c.get_state()['pool_balance'] == 0 and c.get_state()['awarded'] == [11, 11, 10]
    conserved(c.get_state())
