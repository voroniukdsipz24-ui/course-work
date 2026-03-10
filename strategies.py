"""
strategies.py
Патерн Strategy для алгоритмів розрахунку платежів за кредитом.
Кожна конкретна стратегія інкапсулює один метод амортизації.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
import logging

from model import Loan, Payment, PaymentSchedule

logger = logging.getLogger(__name__)


class LoanStrategy(ABC):
    """Абстрактна база: кожна стратегія повинна сформувати PaymentSchedule для Loan."""

    @abstractmethod
    def calculate(self, loan: Loan) -> PaymentSchedule:
        """Обчислює та повертає повний графік погашення кредиту."""
        ...


class AnnuityStrategy(LoanStrategy):
    """
    Фіксований щомісячний платіж — кожен внесок однаковий.
    Співвідношення між основною сумою боргу та відсотками змінюється з часом.
    """

    def calculate(self, loan: Loan) -> PaymentSchedule:
        logger.debug("AnnuityStrategy.calculate: principal=%.2f rate=%.4f n=%d",
                     loan.principal, loan.interest_rate, loan.term_months)

        schedule = PaymentSchedule()
        r   = loan.interest_rate / 100.0 / 12.0
        n   = loan.term_months
        bal = loan.principal

        if r == 0.0:
            monthly = bal / n
            for month in range(1, n + 1):
                bal = max(bal - monthly, 0.0)
                schedule.append(Payment(
                    month             = month,
                    principal_part    = monthly,
                    interest_part     = 0.0,
                    total_payment     = monthly,
                    remaining_balance = bal,
                ))
        else:
            monthly = bal * r * (1.0 + r) ** n / ((1.0 + r) ** n - 1.0)
            for month in range(1, n + 1):
                interest  = bal * r
                principal = monthly - interest
                bal       = max(bal - principal, 0.0)
                schedule.append(Payment(
                    month             = month,
                    principal_part    = principal,
                    interest_part     = interest,
                    total_payment     = monthly,
                    remaining_balance = bal,
                ))

        return schedule


class DifferentiatedStrategy(LoanStrategy):
    """
    Фіксована частина основного боргу щомісяця; відсотки зменшуються зі зменшенням залишку.
    Загальний платіж найбільший у 1-му місяці та найменший в останньому.
    """

    def calculate(self, loan: Loan) -> PaymentSchedule:
        logger.debug("DifferentiatedStrategy.calculate: principal=%.2f rate=%.4f n=%d",
                     loan.principal, loan.interest_rate, loan.term_months)

        schedule   = PaymentSchedule()
        r          = loan.interest_rate / 100.0 / 12.0
        n          = loan.term_months
        principal  = loan.principal / n
        bal        = loan.principal

        for month in range(1, n + 1):
            interest = bal * r
            total    = principal + interest
            bal      = max(bal - principal, 0.0)
            schedule.append(Payment(
                month             = month,
                principal_part    = principal,
                interest_part     = interest,
                total_payment     = total,
                remaining_balance = bal,
            ))

        return schedule


def apply_early_repayment(schedule: PaymentSchedule,
                          loan: Loan,
                          amount: float,
                          at_month: int,
                          strategy: LoanStrategy) -> PaymentSchedule:

    if amount <= 0 or at_month < 1:
        return schedule

    result = PaymentSchedule()

    # копіюємо місяці до дострокового
    for payment in schedule:
        if payment.month < at_month:
            result.append(payment)
        else:
            break

    # отримуємо баланс на момент дострокового
    prev_balance = loan.principal

    if result.month_count > 0:
        last_payment = None
        for p in result:
            last_payment = p
        prev_balance = last_payment.remaining_balance
        new_balance = max(prev_balance - amount, 0.0)

    if new_balance == 0:
        return result

    # створюємо новий Loan з новим залишком
    new_loan = Loan(
        amount=new_balance,
        interest_rate=loan.interest_rate,
        term_months=loan.term_months - at_month,
        loan_type=loan.loan_type,
        down_payment=0,
        commission=0,
        early_repayment_amount=0,
        early_repayment_month=0,
    )

    # перераховуємо хвіст стратегії
    new_schedule = strategy.calculate(new_loan)

    # зсуваємо номери місяців і додаємо
    for payment in new_schedule:
        result.append(Payment(
            month=at_month + payment.month - 1,
            principal_part=payment.principal_part,
            interest_part=payment.interest_part,
            total_payment=payment.total_payment,
            remaining_balance=payment.remaining_balance,
        ))

    return result
