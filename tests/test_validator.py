import pytest
from model import Loan, LoanType
from validator import InputValidator, LoanFormData, ValidationError

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestInputValidator:

    def test_valid_data_returns_loan(self, validator, base_form):
        loan = validator.validate(base_form)
        assert isinstance(loan, Loan)

    def test_valid_data_correct_values(self, validator, base_form):
        loan = validator.validate(base_form)
        assert loan.amount == pytest.approx(100_000.0)
        assert loan.interest_rate == pytest.approx(5.0)
        assert loan.term_months == 12
        assert loan.loan_type == LoanType.ANNUITY

    def test_negative_amount_raises_validation_error(self, validator, base_form):
        base_form.amount = "-1000"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "amount"

    def test_zero_amount_raises_validation_error(self, validator, base_form):
        base_form.amount = "0"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "amount"

    def test_non_numeric_amount_raises_validation_error(self, validator, base_form):
        base_form.amount = "abc"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "amount"

    def test_comma_as_decimal_separator_raises_error(self, validator, base_form):
        base_form.rate = "5,5"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "rate"

    def test_empty_amount_raises_validation_error(self, validator, base_form):
        base_form.amount = ""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "amount"

    def test_rate_above_100_raises_error(self, validator, base_form):
        base_form.rate = "101"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "rate"

    def test_zero_rate_is_valid(self, validator, base_form):
        base_form.rate = "0"
        loan = validator.validate(base_form)
        assert loan.interest_rate == pytest.approx(0.0)

    def test_years_converted_to_months(self, validator, base_form):
        base_form.term = "2"
        base_form.term_in_months = False
        loan = validator.validate(base_form)
        assert loan.term_months == 24

    def test_months_used_directly(self, validator, base_form):
        base_form.term = "18"
        base_form.term_in_months = True
        loan = validator.validate(base_form)
        assert loan.term_months == 18

    def test_down_payment_enabled_and_valid(self, validator, base_form):
        base_form.down_enabled = True
        base_form.down_payment = "10000"
        loan = validator.validate(base_form)
        assert loan.down_payment == pytest.approx(10_000.0)

    def test_down_payment_exceeds_amount_raises_error(self, validator, base_form):
        base_form.down_enabled = True
        base_form.down_payment = "200000"  # > сума 100000
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "down_payment"

    def test_early_month_within_term(self, validator, base_form):
        base_form.early_enabled = True
        base_form.early_amount = "5000"
        base_form.early_month = "6"
        loan = validator.validate(base_form)
        assert loan.early_repayment_month == 6

    def test_early_month_exceeds_term_raises_error(self, validator, base_form):
        base_form.early_enabled = True
        base_form.early_amount = "5000"
        base_form.early_month = "100"  # термін - 12
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "early_month"

    def test_commission_enabled_and_valid(self, validator, base_form):
        base_form.comm_enabled = True
        base_form.commission = "500"
        loan = validator.validate(base_form)
        assert loan.commission == pytest.approx(500.0)

    def test_negative_commission_raises_error(self, validator, base_form):
        base_form.comm_enabled = True
        base_form.commission = "-100"
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "commission"

    def test_disabled_optional_fields_ignored(self, validator, base_form):
        # Поля вимкнені → помилка не повинна виникати навіть якщо значення некоректні
        base_form.down_enabled = False
        base_form.down_payment = "abc"
        base_form.comm_enabled = False
        base_form.commission = "xyz"
        base_form.early_enabled = False
        base_form.early_amount = "bad"
        loan = validator.validate(base_form)
        assert loan.down_payment == 0.0
        assert loan.commission == 0.0

    def test_whitespace_only_amount_raises_error(self, validator, base_form):
        base_form.amount = "   "
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(base_form)
        assert exc_info.value.field == "amount"

    def test_differentiated_loan_type_preserved(self, validator, base_form):
        base_form.loan_type = LoanType.DIFFERENTIATED
        loan = validator.validate(base_form)
        assert loan.loan_type == LoanType.DIFFERENTIATED