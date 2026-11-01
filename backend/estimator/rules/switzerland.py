# Swiss income tax and social security rules for 2026.
# Used for the hypothetical tax: what a single person with no children in the
# city of Zurich would pay on the same salary and bonus, without church tax.

TAX_YEAR = 2026

# --- Social security, employee share (source: ch_ahv_contributions, ch_alv_contributions)
AHV_IV_EO_EMPLOYEE_RATE = 0.053  # AHV 4.35% + IV 0.7% + EO 0.25%
AHV_IV_EO_EMPLOYER_RATE = 0.053
ALV_EMPLOYEE_RATE = 0.011        # unemployment insurance, half of 2.2%
ALV_EMPLOYER_RATE = 0.011
ALV_SALARY_CAP = 148_200         # no ALV on salary above this since 2023

# --- Federal income tax, single taxpayers (source: ch_federal_tariff_2026)
# The ESTV table is defined by breakpoints: from `income` upwards, the tax is
# `base_tax` plus `rate` on every further franc. Values are copied from Form 58c.
FEDERAL_TARIFF_SINGLE = [
    # (income from, tax at that income, marginal rate)
    (0, 0.00, 0.0),
    (15_200, 0.00, 0.0077),
    (33_200, 138.60, 0.0088),
    (43_500, 229.20, 0.0264),
    (58_000, 612.00, 0.0297),
    (76_200, 1_152.50, 0.0594),
    (82_100, 1_502.95, 0.0660),
    (108_900, 3_271.75, 0.0880),
    (141_500, 6_140.55, 0.1100),
    (185_100, 10_936.55, 0.1320),
]
# For high incomes the tax is capped at a flat 11.5% of the whole income.
FEDERAL_MAX_RATE = 0.115

# Federal deductions for an employee (source: ch_federal_deductions_2026)
FEDERAL_PROFESSIONAL_EXPENSES_RATE = 0.03  # of net salary
FEDERAL_PROFESSIONAL_EXPENSES_MIN = 2_000
FEDERAL_PROFESSIONAL_EXPENSES_MAX = 4_000
# Insurance premium deduction, single, member of a pension fund (pillar 2)
FEDERAL_INSURANCE_DEDUCTION = 1_800

# --- Zurich cantonal and communal tax (source: zh_tariff_2026)
# Basic tariff (Grundtarif, § 35 Abs. 1 StG) for the "simple state tax".
# Each entry is (width of band, rate); the last band has no upper limit.
ZURICH_TARIFF_SINGLE = [
    (7_000, 0.00),
    (5_000, 0.02),
    (4_800, 0.03),
    (8_000, 0.04),
    (9_700, 0.05),
    (11_200, 0.06),
    (13_100, 0.07),
    (17_600, 0.08),
    (34_000, 0.09),
    (33_700, 0.10),
    (53_300, 0.11),
    (69_300, 0.12),
    (None, 0.13),
]

# The simple tax is multiplied by the cantonal and communal multipliers.
ZURICH_CANTON_MULTIPLIER = 0.95  # source: zh_cantonal_multiplier
ZURICH_CITY_MULTIPLIER = 1.19    # source: zh_city_multiplier, without church tax
ZURICH_PERSONAL_TAX = 24         # source: zh_personal_tax, flat per adult

# Zurich deductions for an employee (source: zh_deductions_2026)
ZURICH_PROFESSIONAL_EXPENSES_RATE = 0.03
ZURICH_PROFESSIONAL_EXPENSES_MIN = 2_000
ZURICH_PROFESSIONAL_EXPENSES_MAX = 4_000
ZURICH_INSURANCE_DEDUCTION = 2_900

# Both tax authorities ignore taxable income below a full CHF 100.
TAXABLE_INCOME_ROUNDING = 100
