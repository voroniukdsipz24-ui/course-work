import sys
import os
import pytest
from model import Loan, LoanType, Payment, PaymentSchedule
from strategies import AnnuityStrategy, DifferentiatedStrategy
from validator import InputValidator, LoanFormData
from controller import LoanController
from chart_generator import ChartGenerator

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def annuity_loan():
    return Loan(
        amount=100_000.0,
        interest_rate=5.0,
        term_months=12,
        loan_type=LoanType.ANNUITY,
    )


@pytest.fixture
def diff_loan():
    return Loan(
        amount=60_000.0,
        interest_rate=12.0,
        term_months=24,
        loan_type=LoanType.DIFFERENTIATED,
    )


@pytest.fixture
def zero_rate_loan():
    return Loan(
        amount=12_000.0,
        interest_rate=0.0,
        term_months=12,
        loan_type=LoanType.ANNUITY,
    )


@pytest.fixture
def annuity_strategy():
    return AnnuityStrategy()


@pytest.fixture
def diff_strategy():
    return DifferentiatedStrategy()


@pytest.fixture
def validator():
    return InputValidator()


@pytest.fixture
def base_form():
    return LoanFormData(
        amount="100000",
        rate="5",
        term="12",
        term_in_months=True,
        loan_type=LoanType.ANNUITY,
    )


@pytest.fixture
def controller():
    return LoanController()


@pytest.fixture
def chart_generator():
    return ChartGenerator()


@pytest.fixture
def small_schedule():
    s = PaymentSchedule()
    for i in range(1, 4):
        s.append(Payment(
            month=i,
            principal_part=1000.0,
            interest_part=50.0 / i,
            total_payment=1000.0 + 50.0 / i,
            remaining_balance=3000.0 - i * 1000.0,
        ))
    return s