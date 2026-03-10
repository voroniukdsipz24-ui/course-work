import pytest
from model import Loan, LoanType, Payment, PaymentSchedule

# ═══════════════════════════════════════════════════════════════════════════════
# MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPaymentSchedule:

    def test_append_increases_month_count(self):
        s = PaymentSchedule()
        assert s.month_count == 0
        s.append(Payment(1, 100.0, 10.0, 110.0, 900.0))
        assert s.month_count == 1

    def test_total_payment_sums_all_payments(self):
        s = PaymentSchedule()
        s.append(Payment(1, 100.0, 10.0, 110.0, 900.0))
        s.append(Payment(2, 100.0, 8.0, 108.0, 800.0))
        assert s.total_payment == pytest.approx(218.0)

    def test_total_interest_sums_interest_parts(self):
        s = PaymentSchedule()
        s.append(Payment(1, 100.0, 10.0, 110.0, 900.0))
        s.append(Payment(2, 100.0, 8.0, 108.0, 800.0))
        assert s.total_interest == pytest.approx(18.0)

    def test_cache_invalidated_after_append(self):
        s = PaymentSchedule()
        s.append(Payment(1, 100.0, 10.0, 110.0, 900.0))
        _ = s.total_payment   # ініціалізуємо кеш
        s.append(Payment(2, 100.0, 8.0, 108.0, 800.0))
        # Кеш має бути інвалідований → перераховано з урахуванням нового платежу
        assert s.total_payment == pytest.approx(218.0)

    def test_iteration_preserves_order(self):
        s = PaymentSchedule()
        for i in range(1, 5):
            s.append(Payment(i, float(i * 100), 5.0, float(i * 100 + 5), 0.0))
        months = [p.month for p in s]
        assert months == [1, 2, 3, 4]

    def test_len_reflects_payment_count(self):
        s = PaymentSchedule()
        for i in range(1, 7):
            s.append(Payment(i, 100.0, 5.0, 105.0, 0.0))
        assert len(s) == 6

    def test_first_payment_returns_first_total(self):
        s = PaymentSchedule()
        s.append(Payment(1, 900.0, 100.0, 1000.0, 9000.0))
        s.append(Payment(2, 910.0, 90.0, 1000.0, 8090.0))
        assert s.first_payment == pytest.approx(1000.0)

    def test_empty_schedule_first_payment_is_zero(self):
        assert PaymentSchedule().first_payment == 0.0

    def test_empty_schedule_totals_are_zero(self):
        s = PaymentSchedule()
        assert s.total_payment == 0.0
        assert s.total_interest == 0.0


class TestLoan:

    def test_principal_subtracts_down_payment(self):
        loan = Loan(amount=200_000, interest_rate=5.0, term_months=24,
                    loan_type=LoanType.ANNUITY, down_payment=20_000)
        assert loan.principal == pytest.approx(180_000.0)

    def test_principal_without_down_payment(self):
        loan = Loan(amount=100_000, interest_rate=5.0, term_months=12,
                    loan_type=LoanType.ANNUITY)
        assert loan.principal == pytest.approx(100_000.0)