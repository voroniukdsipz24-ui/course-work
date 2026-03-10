"""
model.py
Доменна модель для кредитного калькулятора.
Містить лише класи даних без залежностей від Qt або механізмів відображення.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LoanType(Enum):
    ANNUITY       = "Annuity"
    DIFFERENTIATED = "Differentiated"


@dataclass
class Loan:
    """Представляє конфігурацію кредиту, введену користувачем."""
    amount:       float
    interest_rate: float          # річний, відсоток (наприклад, 5.5 означає 5.5%)
    term_months:  int
    loan_type:    LoanType
    down_payment: float = 0.0
    commission:   float = 0.0
    early_repayment_amount: float = 0.0
    early_repayment_month:  int   = 0

    @property
    def principal(self) -> float:
        return self.amount - self.down_payment


@dataclass
class Payment:
    """Представляє один щомісячний платіж у графіку погашення кредиту."""
    month:             int
    principal_part:    float
    interest_part:     float
    total_payment:     float
    remaining_balance: float


@dataclass
class PaymentSchedule:
    """
    Упорядкований список платежів.
    Обчислює загальні підсумки за потреби та кешує результат.
    """
    payments: list[Payment] = field(default_factory=list)

    # ── кешовані агрегати ────────────────────────────────────────────────────
    _total_payment_cache:  float | None = field(default=None, init=False, repr=False, compare=False)
    _total_interest_cache: float | None = field(default=None, init=False, repr=False, compare=False)

    def _invalidate_cache(self) -> None:
        self._total_payment_cache  = None
        self._total_interest_cache = None

    def append(self, payment: Payment) -> None:
        self.payments.append(payment)
        self._invalidate_cache()

    @property
    def total_payment(self) -> float:
        if self._total_payment_cache is None:
            self._total_payment_cache = sum(p.total_payment for p in self.payments)
        return self._total_payment_cache

    @property
    def total_interest(self) -> float:
        if self._total_interest_cache is None:
            self._total_interest_cache = sum(p.interest_part for p in self.payments)
        return self._total_interest_cache

    @property
    def month_count(self) -> int:
        return len(self.payments)

    @property
    def first_payment(self) -> float:
        return self.payments[0].total_payment if self.payments else 0.0

    def __len__(self) -> int:
        return len(self.payments)

    def __iter__(self):
        return iter(self.payments)
