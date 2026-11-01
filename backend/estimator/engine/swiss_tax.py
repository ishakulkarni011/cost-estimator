# Hypothetical Swiss tax and social security for a single person in the city of Zurich.

from dataclasses import dataclass

from ..rules import switzerland as rules
from .money import ZERO, dec, floor_to


@dataclass
class SocialSecurity:
    ahv_iv_eo: object
    alv: object

    @property
    def total(self):
        return self.ahv_iv_eo + self.alv


def employee_social_security(salary):
    salary = dec(salary)
    return SocialSecurity(
        ahv_iv_eo=salary * dec(rules.AHV_IV_EO_EMPLOYEE_RATE),
        alv=min(salary, dec(rules.ALV_SALARY_CAP)) * dec(rules.ALV_EMPLOYEE_RATE),
    )


def employer_social_security(salary):
    salary = dec(salary)
    return SocialSecurity(
        ahv_iv_eo=salary * dec(rules.AHV_IV_EO_EMPLOYER_RATE),
        alv=min(salary, dec(rules.ALV_SALARY_CAP)) * dec(rules.ALV_EMPLOYER_RATE),
    )


# Direct federal tax for a single taxpayer, from the ESTV 2026 table.
def federal_tax(taxable_income):
    income = floor_to(max(ZERO, dec(taxable_income)), rules.TAXABLE_INCOME_ROUNDING)
    tax = ZERO
    # Find the highest breakpoint at or below the income
    for start, base_tax, rate in rules.FEDERAL_TARIFF_SINGLE:
        if income >= start:
            tax = dec(base_tax) + (income - start) * dec(rate)
    tax = min(tax, income * dec(rules.FEDERAL_MAX_RATE))
    # The annual tax is rounded down to the next 5 Rappen.
    return floor_to(tax, "0.05")


# The simple state tax (einfache Staatssteuer) from the Zurich basic tariff.
def zurich_simple_tax(taxable_income):
    remaining = floor_to(max(ZERO, dec(taxable_income)), rules.TAXABLE_INCOME_ROUNDING)
    tax = ZERO
    # Fill each band in turn until the income runs out
    for width, rate in rules.ZURICH_TARIFF_SINGLE:
        in_band = remaining if width is None else min(remaining, dec(width))
        tax += in_band * dec(rate)
        remaining -= in_band
        if remaining <= 0:
            break
    return tax


@dataclass
class ZurichTax:
    simple_tax: object
    cantonal: object
    communal: object
    personal_tax: object

    @property
    def total(self):
        return self.cantonal + self.communal + self.personal_tax


def zurich_tax(taxable_income):
    simple = zurich_simple_tax(taxable_income)
    return ZurichTax(
        simple_tax=simple,
        cantonal=floor_to(simple * dec(rules.ZURICH_CANTON_MULTIPLIER), "0.05"),
        communal=floor_to(simple * dec(rules.ZURICH_CITY_MULTIPLIER), "0.05"),
        personal_tax=dec(rules.ZURICH_PERSONAL_TAX),
    )


def _professional_expenses(net_salary, rate, minimum, maximum):
    return min(max(net_salary * dec(rate), dec(minimum)), dec(maximum))


@dataclass
class HypotheticalSwissTax:
    gross_salary: object
    social_security: SocialSecurity
    federal_professional_expenses: object
    federal_insurance_deduction: object
    federal_taxable_income: object
    federal_tax: object
    zurich_professional_expenses: object
    zurich_insurance_deduction: object
    zurich_taxable_income: object
    zurich: ZurichTax

    @property
    def total(self):
        return self.federal_tax + self.zurich.total


# Income tax a single person in the city of Zurich would pay on this salary.
# Deducts employee social security, flat 3% professional expenses and the
# insurance premium allowance. No church tax, pension fund or pillar 3a.
def hypothetical_tax(gross_salary):
    gross_salary = dec(gross_salary)
    social_security = employee_social_security(gross_salary)
    net_salary = gross_salary - social_security.total

    # Federal taxable income
    federal_expenses = _professional_expenses(
        net_salary,
        rules.FEDERAL_PROFESSIONAL_EXPENSES_RATE,
        rules.FEDERAL_PROFESSIONAL_EXPENSES_MIN,
        rules.FEDERAL_PROFESSIONAL_EXPENSES_MAX,
    )
    federal_insurance = min(dec(rules.FEDERAL_INSURANCE_DEDUCTION), net_salary)
    federal_taxable = floor_to(
        max(ZERO, net_salary - federal_expenses - federal_insurance), rules.TAXABLE_INCOME_ROUNDING
    )

    # Zurich taxable income uses the same steps with its own allowances
    zurich_expenses = _professional_expenses(
        net_salary,
        rules.ZURICH_PROFESSIONAL_EXPENSES_RATE,
        rules.ZURICH_PROFESSIONAL_EXPENSES_MIN,
        rules.ZURICH_PROFESSIONAL_EXPENSES_MAX,
    )
    zurich_insurance = min(dec(rules.ZURICH_INSURANCE_DEDUCTION), net_salary)
    zurich_taxable = floor_to(
        max(ZERO, net_salary - zurich_expenses - zurich_insurance), rules.TAXABLE_INCOME_ROUNDING
    )

    return HypotheticalSwissTax(
        gross_salary=gross_salary,
        social_security=social_security,
        federal_professional_expenses=federal_expenses,
        federal_insurance_deduction=federal_insurance,
        federal_taxable_income=federal_taxable,
        federal_tax=federal_tax(federal_taxable),
        zurich_professional_expenses=zurich_expenses,
        zurich_insurance_deduction=zurich_insurance,
        zurich_taxable_income=zurich_taxable,
        zurich=zurich_tax(zurich_taxable),
    )
