# UK income tax and Class 1 National Insurance for one tax year.

from dataclasses import dataclass, field

from ..rules import uk as rules
from .money import ZERO, dec

BAND_NAMES = ["Basic rate", "Higher rate", "Additional rate"]


@dataclass
class BandTax:
    name: str
    rate: object
    income_in_band: object
    tax: object


@dataclass
class IncomeTaxBreakdown:
    income: object
    personal_allowance: object
    taxable_income: object
    bands: list = field(default_factory=list)

    @property
    def total(self):
        return sum((band.tax for band in self.bands), ZERO)


# £12,570, reduced by £1 for every £2 of income over £100,000.
def personal_allowance(income):
    excess = max(ZERO, dec(income) - rules.ALLOWANCE_TAPER_THRESHOLD)
    return max(ZERO, rules.PERSONAL_ALLOWANCE - excess / 2)


def income_tax_breakdown(income):
    income = dec(income)
    allowance = min(personal_allowance(income), income)
    taxable = max(ZERO, income - allowance)

    result = IncomeTaxBreakdown(income=income, personal_allowance=allowance, taxable_income=taxable)
    # Slice the taxable income across the basic, higher and additional bands
    lower = ZERO
    for name, (upper, rate) in zip(BAND_NAMES, rules.INCOME_TAX_BANDS):
        upper = taxable if upper is None else min(dec(upper), taxable)
        in_band = max(ZERO, upper - lower)
        result.bands.append(BandTax(name, dec(rate), in_band, in_band * dec(rate)))
        lower = max(lower, upper)
    return result


def income_tax(income):
    return income_tax_breakdown(income).total


# Class 1 employee contributions (category A) on annual earnings.
def employee_ni(earnings):
    earnings = dec(earnings)
    main_band = max(ZERO, min(earnings, dec(rules.NI_UPPER_EARNINGS_LIMIT)) - rules.NI_PRIMARY_THRESHOLD)
    upper_band = max(ZERO, earnings - rules.NI_UPPER_EARNINGS_LIMIT)
    return main_band * dec(rules.NI_EMPLOYEE_MAIN_RATE) + upper_band * dec(rules.NI_EMPLOYEE_UPPER_RATE)


# Class 1 secondary (employer) contributions on annual cash earnings.
def employer_ni(earnings):
    return max(ZERO, dec(earnings) - rules.NI_SECONDARY_THRESHOLD) * dec(rules.NI_EMPLOYER_RATE)


def employer_class_1a(benefits_in_kind):
    return max(ZERO, dec(benefits_in_kind)) * dec(rules.NI_CLASS_1A_RATE)
