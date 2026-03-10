import pytest
from unittest.mock import MagicMock

from model import LoanType, Loan, PaymentSchedule
from controller import LoanController

# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLLER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoanController:

    def test_success_callback_called_with_valid_data(self, controller, base_form):
        success_cb = MagicMock()
        controller.on_success(success_cb)
        controller.calculate(base_form)
        success_cb.assert_called_once()

    def test_success_callback_receives_loan_and_schedule(self, controller, base_form):
        captured = {}
        def on_success(loan, schedule):
            captured["loan"] = loan
            captured["schedule"] = schedule

        controller.on_success(on_success)
        controller.calculate(base_form)
        assert isinstance(captured["loan"], Loan)
        assert isinstance(captured["schedule"], PaymentSchedule)
        assert captured["schedule"].month_count > 0

    def test_validation_error_callback_called_on_bad_data(self, controller, base_form):
        error_cb = MagicMock()
        controller.on_validation_error(error_cb)
        base_form.amount = "not_a_number"
        controller.calculate(base_form)
        error_cb.assert_called_once()

    def test_validation_error_callback_receives_field_and_message(
            self, controller, base_form):
        captured = {}
        def on_error(field, message):
            captured["field"] = field
            captured["message"] = message

        controller.on_validation_error(on_error)
        base_form.amount = "-500"
        controller.calculate(base_form)
        assert captured["field"] == "amount"
        assert isinstance(captured["message"], str)

    def test_success_callback_not_called_on_validation_error(
            self, controller, base_form):
        success_cb = MagicMock()
        controller.on_success(success_cb)
        base_form.rate = "abc"
        controller.calculate(base_form)
        success_cb.assert_not_called()

    def test_error_callback_not_called_on_success(self, controller, base_form):
        error_cb = MagicMock()
        controller.on_validation_error(error_cb)
        controller.calculate(base_form)
        error_cb.assert_not_called()

    def test_get_last_schedule_after_calculate(self, controller, base_form):
        controller.calculate(base_form)
        assert controller.get_last_schedule() is not None

    def test_reset_clears_last_schedule(self, controller, base_form):
        controller.calculate(base_form)
        controller.reset()
        assert controller.get_last_schedule() is None

    def test_reset_clears_chart_generator_cache(self, controller, base_form):
        controller.calculate(base_form)
        controller.reset()
        cg = controller.get_chart_generator()
        assert cg._cache_key is None

    def test_no_callbacks_registered_does_not_raise(self, controller, base_form):
        """Контролер має працювати коректно навіть без зареєстрованих callback-ів."""
        controller.calculate(base_form)  # виняток не очікується

    def test_annuity_strategy_selected_for_annuity_loan(self, controller, base_form):
        base_form.loan_type = LoanType.ANNUITY
        controller.calculate(base_form)
        schedule = controller.get_last_schedule()
        # Для ануїтетного кредиту всі total_payments мають бути приблизно однакові
        totals = [p.total_payment for p in schedule]
        assert max(totals) - min(totals) < 0.02

    def test_differentiated_strategy_selected_for_diff_loan(self, controller, base_form):
        base_form.loan_type = LoanType.DIFFERENTIATED
        controller.calculate(base_form)
        schedule = controller.get_last_schedule()
        # Для диференційованого кредиту перший платіж > останній платіж
        assert schedule.payments[0].total_payment > schedule.payments[-1].total_payment

    def test_export_csv_when_no_schedule_does_not_raise(self, controller, tmp_path):
        path = str(tmp_path / "export.csv")
        controller.export_schedule_csv(path)  # має записати попередження в лог

    def test_export_csv_creates_file(self, controller, base_form, tmp_path):
        controller.calculate(base_form)
        path = str(tmp_path / "schedule.csv")
        controller.export_schedule_csv(path)
        import os
        assert os.path.exists(path)

    def test_export_csv_has_correct_headers(self, controller, base_form, tmp_path):
        controller.calculate(base_form)
        path = str(tmp_path / "schedule.csv")
        controller.export_schedule_csv(path)
        with open(path) as f:
            header = f.readline().strip()
        assert "Місяць" in header
        assert "Залишок" in header
        assert "Відсотки" in header