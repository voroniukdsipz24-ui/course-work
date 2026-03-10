import pytest
from model import Loan, LoanType
from strategies import (
    AnnuityStrategy,
    DifferentiatedStrategy,
    apply_early_repayment,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STRATEGY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnnuityStrategy:

    def test_payment_count_matches_term(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        assert schedule.month_count == annuity_loan.term_months

    def test_all_payments_equal(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        payments = [p.total_payment for p in schedule]
        assert max(payments) - min(payments) < 0.01  # допустима похибка округлення

    def test_zero_rate_no_interest(self, annuity_strategy, zero_rate_loan):
        schedule = annuity_strategy.calculate(zero_rate_loan)
        for p in schedule:
            assert p.interest_part == pytest.approx(0.0)

    def test_zero_rate_equal_principal_parts(self, annuity_strategy, zero_rate_loan):
        schedule = annuity_strategy.calculate(zero_rate_loan)
        expected = zero_rate_loan.principal / zero_rate_loan.term_months
        for p in schedule:
            assert p.principal_part == pytest.approx(expected, rel=1e-6)

    def test_positive_interest_overpayment(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        assert schedule.total_payment > annuity_loan.principal

    def test_final_balance_near_zero(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        assert schedule.payments[-1].remaining_balance == pytest.approx(0.0, abs=0.01)

    def test_balance_monotonically_decreasing(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        balances = [p.remaining_balance for p in schedule]
        for a, b in zip(balances, balances[1:]):
            assert a >= b

    def test_principal_plus_interest_equals_payment(self, annuity_strategy, annuity_loan):
        schedule = annuity_strategy.calculate(annuity_loan)
        for p in schedule:
            assert p.principal_part + p.interest_part == pytest.approx(p.total_payment, rel=1e-6)

    def test_single_month_loan(self, annuity_strategy):
        loan = Loan(amount=1000, interest_rate=12.0, term_months=1,
                    loan_type=LoanType.ANNUITY)
        schedule = annuity_strategy.calculate(loan)
        assert schedule.month_count == 1
        # Загальний платіж ≈ основна сума боргу + відсотки за 1 місяць
        assert schedule.payments[0].total_payment == pytest.approx(
            1000 * (0.01 * 1.01 / (1.01 - 1)), rel=1e-4
        )

    def test_long_term_loan(self, annuity_strategy):
        loan = Loan(amount=500_000, interest_rate=7.0, term_months=360,
                    loan_type=LoanType.ANNUITY)
        schedule = annuity_strategy.calculate(loan)
        assert schedule.month_count == 360
        assert schedule.total_interest > 0


class TestDifferentiatedStrategy:

    def test_payment_count_matches_term(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        assert schedule.month_count == diff_loan.term_months

    def test_payments_decrease_over_time(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        totals = [p.total_payment for p in schedule]
        # Кожен платіж має бути більше наступного (строго для ненульової ставки)
        for a, b in zip(totals, totals[1:]):
            assert a >= b - 0.01  # невелика похибка для чисел з плаваючим значенням

    def test_principal_part_is_constant(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        expected = diff_loan.principal / diff_loan.term_months
        for p in schedule:
            assert p.principal_part == pytest.approx(expected, rel=1e-6)

    def test_interest_decreases_over_time(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        interests = [p.interest_part for p in schedule]
        for a, b in zip(interests, interests[1:]):
            assert a >= b - 0.01

    def test_final_balance_near_zero(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        assert schedule.payments[-1].remaining_balance == pytest.approx(0.0, abs=0.01)

    def test_total_payment_exceeds_principal(self, diff_strategy, diff_loan):
        schedule = diff_strategy.calculate(diff_loan)
        assert schedule.total_payment > diff_loan.principal

    def test_zero_rate_payment_equals_principal_part(self, diff_strategy):
        loan = Loan(amount=12_000, interest_rate=0.0, term_months=12,
                    loan_type=LoanType.DIFFERENTIATED)
        schedule = diff_strategy.calculate(loan)
        for p in schedule:
            assert p.interest_part == pytest.approx(0.0)
            assert p.total_payment == pytest.approx(p.principal_part)


class TestEarlyRepayment:

    def test_early_repayment_shortens_schedule(self, annuity_strategy, annuity_loan):
        full_schedule = annuity_strategy.calculate(annuity_loan)
        early_schedule = apply_early_repayment(
            full_schedule, annuity_loan,
            amount=50_000.0, at_month=6,
            strategy=annuity_strategy,
        )
        assert early_schedule.month_count < full_schedule.month_count

    def test_early_repayment_zero_amount_returns_original(
            self, annuity_strategy, annuity_loan):
        full_schedule = annuity_strategy.calculate(annuity_loan)
        result = apply_early_repayment(
            full_schedule, annuity_loan,
            amount=0.0, at_month=3,
            strategy=annuity_strategy,
        )
        assert result is full_schedule

    def test_early_repayment_invalid_month_returns_original(
            self, annuity_strategy, annuity_loan):
        full_schedule = annuity_strategy.calculate(annuity_loan)
        result = apply_early_repayment(
            full_schedule, annuity_loan,
            amount=10_000.0, at_month=0,
            strategy=annuity_strategy,
        )
        assert result is full_schedule

    def test_early_repayment_prefix_preserved(self, annuity_strategy, annuity_loan):
        full_schedule = annuity_strategy.calculate(annuity_loan)
        at_month = 4
        result = apply_early_repayment(
            full_schedule, annuity_loan,
            amount=20_000.0, at_month=at_month,
            strategy=annuity_strategy,
        )
        # місяці 1..at_month-1 мають бути ідентичними
        for orig, new in zip(full_schedule.payments[:at_month - 1], result.payments[:at_month - 1]):
            assert orig.month == new.month
            assert orig.total_payment == pytest.approx(new.total_payment, rel=1e-6)

    def test_early_repayment_with_diff_strategy(self, diff_strategy, diff_loan):
        full_schedule = diff_strategy.calculate(diff_loan)
        result = apply_early_repayment(
            full_schedule, diff_loan,
            amount=20_000.0, at_month=6,
            strategy=diff_strategy,
        )
        assert result.month_count < full_schedule.month_count
