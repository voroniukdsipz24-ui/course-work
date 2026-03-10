"""
validator.py
Сервіс перевірки вхідних даних.
Відокремлений як від віджетів Qt, так і від бізнес-логіки.
"""

from __future__ import annotations
from dataclasses import dataclass
import logging

from model import Loan, LoanType

logger = logging.getLogger(__name__)

class ValidationError(ValueError):
    """Викликається InputValidator, коли поле містить некоректне значення"""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field   = field
        self.message = message


@dataclass
class LoanFormData:
    """Рядкові значення, зібрані з інтерфейсу"""
    amount:       str
    rate:         str
    term:         str
    term_in_months: bool          # True → поле term вже задане в місяцях
    loan_type:    LoanType
    down_payment: str = ""
    down_enabled: bool = False
    commission:   str = ""
    comm_enabled: bool = False
    early_amount: str = ""
    early_month:  str = ""
    early_enabled: bool = False


class InputValidator:
    """
    Перетворює LoanFormData на валідований датаклас Loan.
    Викликає ValidationError (з установленим .field) при першій некоректній вхідній величині.
    """

    FIELD_NAMES = {
        "amount": "Сума кредиту",
        "rate": "Відсоткова ставка",
        "term": "Термін",
        "down_payment": "Початковий внесок",
        "commission": "Комісія",
        "early_amount": "Сума дострокового погашення",
        "early_month": "Місяць дострокового погашення",
    }

    def validate(self, data: LoanFormData) -> Loan:
        logger.debug("Validating form data")

        amount   = self._parse("amount",  data.amount,   min_v=1.0)
        rate     = self._parse("rate",    data.rate,     min_v=0.0, max_v=100.0)
        term_raw = self._parse("term",    data.term,     min_v=1.0)

        if not term_raw.is_integer():
            raise ValidationError(
                "term",
                "Термін кредиту має бути цілим числом."
            )

        n = int(round(term_raw)) if data.term_in_months else int(round(term_raw * 12))

        if n < 1:
            raise ValidationError("term", "Термін кредиту має становити щонайменше 1 місяць.")

        if n > 600:
            raise ValidationError("term", "Максимальний термін кредиту 50 років або 600 місяців.")

        down = 0.0
        if data.down_enabled and data.down_payment.strip():
            down = self._parse("down_payment", data.down_payment, min_v=0.0, max_v=amount)

        comm = 0.0
        if data.comm_enabled and data.commission.strip():
            comm = self._parse("commission", data.commission, min_v=0.0)

        early_amount = 0.0
        early_month  = 0
        if data.early_enabled and data.early_amount.strip():
            early_amount = self._parse("early_amount", data.early_amount, min_v=0.0)
            early_month  = int(self._parse("early_month", data.early_month, min_v=1.0, max_v=n))

        loan = Loan(
            amount                 = amount,
            interest_rate          = rate,
            term_months            = n,
            loan_type              = data.loan_type,
            down_payment           = down,
            commission             = comm,
            early_repayment_amount = early_amount,
            early_repayment_month  = early_month,
        )
        logger.info("Validation passed: %s", loan)
        return loan

    @staticmethod
    def _parse(field: str, text: str, min_v: float = 0.0,
               max_v: float | None = None) -> float:

        name = InputValidator.FIELD_NAMES.get(field, field)
        clean = text.strip()

        if not clean:
            raise ValidationError(
                field,
                f"{name} є обов’язковим полем."
            )

        if "," in clean:
            raise ValidationError(
                field,
                f"{name}: використовуйте крапку як десятковий роздільник (наприклад, 3.5)."
            )

        try:
            v = float(clean)
        except ValueError:
            raise ValidationError(
                field,
                f"{name}: введіть коректне числове значення."
            )

        if v < min_v:
            raise ValidationError(
                field,
                f"{name} не може бути меншим за {min_v}."
            )

        if max_v is not None and v > max_v:
            raise ValidationError(
                field,
                f"{name} не може перевищувати {max_v:,.2f}."
            )

        return v