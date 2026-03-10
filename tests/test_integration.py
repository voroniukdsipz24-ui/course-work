import pytest

from model import LoanType
from validator import InputValidator, LoanFormData
from strategies import AnnuityStrategy, DifferentiatedStrategy, apply_early_repayment
from controller import LoanController

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION / CROSS-COMPONENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:

    def test_validator_to_strategy_annuity_full_pipeline(self):
        validator = InputValidator()
        form = LoanFormData(
            amount="200000", rate="6", term="2",
            term_in_months=False, loan_type=LoanType.ANNUITY,
        )
        loan = validator.validate(form)
        schedule = AnnuityStrategy().calculate(loan)
        assert schedule.month_count == 24
        assert schedule.payments[-1].remaining_balance == pytest.approx(0.0, abs=0.02)

    def test_validator_to_strategy_differentiated_full_pipeline(self):
        validator = InputValidator()
        form = LoanFormData(
            amount="50000", rate="8", term="12",
            term_in_months=True, loan_type=LoanType.DIFFERENTIATED,
        )
        loan = validator.validate(form)
        schedule = DifferentiatedStrategy().calculate(loan)
        assert schedule.month_count == 12
        first_total = schedule.payments[0].total_payment
        last_total = schedule.payments[-1].total_payment
        assert first_total > last_total

    def test_controller_produces_correct_month_count(self):
        controller = LoanController()
        form = LoanFormData(
            amount="120000", rate="5", term="10",
            term_in_months=False, loan_type=LoanType.ANNUITY,
        )
        controller.calculate(form)
        assert controller.get_last_schedule().month_count == 120

    def test_early_repayment_full_pipeline(self):
        """Наскрізний тест: валідація → стратегія → дострокове погашення → коротший графік."""
        validator = InputValidator()
        form = LoanFormData(
            amount="100000", rate="7", term="24",
            term_in_months=True, loan_type=LoanType.ANNUITY,
            early_enabled=True, early_amount="30000", early_month="12",
        )
        loan = validator.validate(form)
        strategy = AnnuityStrategy()
        full = strategy.calculate(loan)
        short = apply_early_repayment(full, loan, loan.early_repayment_amount,
                                      loan.early_repayment_month, strategy)
        assert short.month_count < full.month_count