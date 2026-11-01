# UK income tax, National Insurance and benefit rules for tax year 2026/27.
# England, Wales and Northern Ireland rates (London), used for every assignment year.

TAX_YEAR = "2026/27"

# Income tax (source: uk_income_tax_rates, uk_employer_rates_2026_27)
PERSONAL_ALLOWANCE = 12_570
# Personal allowance goes down by £1 for every £2 of income above this.
ALLOWANCE_TAPER_THRESHOLD = 100_000

# Bands on taxable income, i.e. income after the personal allowance.
# Each entry is (upper limit of band, rate); None means no upper limit.
INCOME_TAX_BANDS = [
    (37_700, 0.20),   # basic rate
    (125_140, 0.40),  # higher rate
    (None, 0.45),     # additional rate
]

# Class 1 National Insurance (source: uk_employer_rates_2026_27).
# Only applies when the employee is in the UK social security system.
NI_PRIMARY_THRESHOLD = 12_570
NI_UPPER_EARNINGS_LIMIT = 50_270
NI_EMPLOYEE_MAIN_RATE = 0.08
NI_EMPLOYEE_UPPER_RATE = 0.02
NI_SECONDARY_THRESHOLD = 5_000
NI_EMPLOYER_RATE = 0.15
NI_CLASS_1A_RATE = 0.15  # on taxable benefits in kind

# Qualifying removal expenses are exempt up to this amount per move
# (source: uk_relocation_exemption, uk_removal_temporary_accommodation).
RELOCATION_EXEMPTION = 8_000
