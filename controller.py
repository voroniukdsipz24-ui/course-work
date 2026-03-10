"""
controller.py
LoanController: єдиний посередник між UserInterface та доменною моделлю.
Отримує дані форми з view, виконує валідацію + стратегію,
і передає результати назад через callback-и, зареєстровані view.
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Callable
import csv

from model import Loan, LoanType, PaymentSchedule
from strategies import AnnuityStrategy, DifferentiatedStrategy, apply_early_repayment
from validator import InputValidator, LoanFormData, ValidationError
from chart_generator import ChartGenerator

logger = logging.getLogger(__name__)


class LoanController:
    """
    Координує: View → Validator → Strategy → ChartGenerator → View.

    View реєструє callback-и; контролер ніколи не імпортує жоден символ Qt.
    """

    _STRATEGIES = {
        LoanType.ANNUITY:        AnnuityStrategy(),
        LoanType.DIFFERENTIATED: DifferentiatedStrategy(),
    }

    def __init__(self) -> None:
        self._validator       = InputValidator()
        self._chart_generator = ChartGenerator()
        self._last_schedule:  PaymentSchedule | None = None
        self._last_loan:      Loan             | None = None

        # ── зворотні виклики, встановлені view ────────────────────────────────────────
        self._on_success:         Callable[[Loan, PaymentSchedule], None] | None = None
        self._on_validation_error: Callable[[str, str], None]             | None = None

    # ── API реєстрації (викликається один раз у UserInterface.init) ─────────────

    def on_success(self, callback: Callable[[Loan, PaymentSchedule], None]) -> None:
        self._on_success = callback

    def on_validation_error(self, callback: Callable[[str, str], None]) -> None:
        self._on_validation_error = callback

    # ── API команд (викликається UserInterface під час дій користувача) ─────────────────

    def calculate(self, form: LoanFormData) -> None:
        logger.info("Controller.calculate called")
        try:
            loan     = self._validator.validate(form)
            schedule = self._run_strategy(loan)

            self._last_loan     = loan
            self._last_schedule = schedule
            self._chart_generator.invalidate_cache()

            if self._on_success:
                self._on_success(loan, schedule)

        except ValidationError as exc:
            logger.warning("Validation error on field '%s': %s", exc.field, exc.message)
            if self._on_validation_error:
                self._on_validation_error(exc.field, exc.message)

    def reset(self) -> None:
        logger.info("Controller.reset called")
        self._last_schedule = None
        self._last_loan     = None
        self._chart_generator.invalidate_cache()

    def get_chart_generator(self) -> ChartGenerator:
        return self._chart_generator

    def get_last_schedule(self) -> PaymentSchedule | None:
        return self._last_schedule

    def export_schedule_csv(self, path: str) -> None:
        if not self._last_schedule:
            logger.warning("export_schedule_csv: no schedule available")
            return

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                "Місяць",
                "Залишок боргу",
                "Тіло кредиту",
                "Відсотки",
                "Платіж"
            ])

            for p in self._last_schedule:
                writer.writerow([
                    p.month,
                    f"{p.remaining_balance:,.2f}",
                    f"{p.principal_part:,.2f}",
                    f"{p.interest_part:,.2f}",
                    f"{p.total_payment:,.2f}"
                ])

        logger.info("CSV exported to %s", path)

    # ── приватні допоміжні функції ───────────────────────────────────────────────────────

    def _run_strategy(self, loan: Loan) -> PaymentSchedule:
        strategy = self._STRATEGIES[loan.loan_type]
        schedule = strategy.calculate(loan)

        if loan.early_repayment_amount > 0:
            schedule = apply_early_repayment(
                schedule,
                loan,
                loan.early_repayment_amount,
                loan.early_repayment_month,
                strategy
            )

        logger.info("Strategy %s produced %d payments; total=%.2f interest=%.2f",
                    loan.loan_type.value,
                    schedule.month_count,
                    schedule.total_payment,
                    schedule.total_interest)
        return schedule
