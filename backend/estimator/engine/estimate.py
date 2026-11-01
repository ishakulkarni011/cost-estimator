# Builds the year-by-year cost of an assignment to the employer.
# Under tax equalisation the employee keeps their Swiss net pay, and the
# employer pays all UK tax due on top, including the tax on that tax.

from dataclasses import dataclass, field

from ..rules import uk as uk_rules
from . import swiss_tax, uk_tax
from .benefits import BENEFIT_IN_KIND, QUALIFYING_RELOCATION, TAXABLE_CASH, TREATMENT_LABELS, TREATMENT_SOURCES
from .benefits import apply_uk_treatment
from .grossup import gross_up
from .money import ZERO, chf_to_gbp, dec
from .social_security import determine_regime

HOME_PAY = "Home pay"
BENEFITS = "Assignment benefits"
HOST_TAX = "Host tax and charges paid by the employer"
DEDUCTIONS = "Deductions"
SECTIONS = [HOME_PAY, BENEFITS, HOST_TAX, DEDUCTIONS]

# One plain-language line per section, shown in the results
SECTION_DESCRIPTIONS = {
    HOME_PAY: "What the employee would earn at home, converted to pounds.",
    BENEFITS: "Extra costs of the move and of living in London, paid by the employer.",
    HOST_TAX: "Tax and social security the employer pays on the employee's behalf.",
    DEDUCTIONS: "Tax the employee would have paid at home anyway. It comes out of their pay, "
                "so it lowers the employer's cost.",
}


@dataclass
class AssignmentInput:
    home_country: str
    host_country: str
    start_date: object
    end_date: object
    years: int
    duration_months: int
    base_salary_chf: object
    bonus_chf: object
    chf_per_gbp: object
    benefits: list = field(default_factory=list)


@dataclass
class Row:
    section: str
    label: str
    amounts: list  # GBP, one per assignment year
    tag: str = ""
    note: str = ""
    sources: list = field(default_factory=list)

    @property
    def total(self):
        return sum(self.amounts, ZERO)


# Intermediate figures for one year, shown so the result can be checked.
@dataclass
class YearWorking:
    hypothetical: object
    net_home_pay_gbp: object
    taxable_benefits_gbp: object
    grossup: object
    uk_tax_on_net: object
    uk_tax_at_gross: object
    employee_ni: object


@dataclass
class Estimate:
    data: AssignmentInput
    regime: object
    rows: list
    working: list
    assumptions: list

    def section_rows(self, section):
        return [row for row in self.rows if row.section == section]

    def year_totals(self):
        return [sum((row.amounts[y] for row in self.rows), ZERO) for y in range(self.data.years)]

    def home_pay_totals(self):
        rows = self.section_rows(HOME_PAY)
        return [sum((row.amounts[y] for row in rows), ZERO) for y in range(self.data.years)]

    @property
    def total(self):
        return sum(self.year_totals(), ZERO)

    # Total employer cost as a multiple of home pay, per year and overall.
    def multiples(self):
        per_year = [cost / home if home else ZERO for cost, home in zip(self.year_totals(), self.home_pay_totals())]
        home_total = sum(self.home_pay_totals(), ZERO)
        return per_year, (self.total / home_total if home_total else ZERO)


# Taxes the employer covers on a given gross UK income. Under the Swiss regime
# this is income tax only. Under the UK regime the employee's Class 1 NI is
# added too, charged on cash pay only (benefits in kind attract Class 1A).
def _uk_tax_function(regime, benefits_in_kind):
    if regime.country == "CH":
        return uk_tax.income_tax

    def taxes(gross_income):
        return uk_tax.income_tax(gross_income) + uk_tax.employee_ni(gross_income - benefits_in_kind)

    return taxes


def build_estimate(data):
    regime = determine_regime(data.duration_months)
    fx = dec(data.chf_per_gbp)
    home_pay_chf = dec(data.base_salary_chf) + dec(data.bonus_chf)

    rows = {}
    working = []
    exemption_left = dec(uk_rules.RELOCATION_EXEMPTION)

    # Each row holds one amount per year; add() fills in a single year
    def add(key, section, label, year, amount, **extra):
        if key not in rows:
            rows[key] = Row(section, label, [ZERO] * data.years, **extra)
        rows[key].amounts[year] = amount

    for year in range(data.years):
        # 1. Home pay
        add("salary", HOME_PAY, "Base salary", year, chf_to_gbp(data.base_salary_chf, fx))
        add("bonus", HOME_PAY, "Bonus", year, chf_to_gbp(data.bonus_chf, fx))

        # 2. Assignment benefits
        taxed_benefits, exemption_left = apply_uk_treatment(data.benefits, year, fx, exemption_left)
        cash_taxable = ZERO
        in_kind_taxable = ZERO
        for index, item in enumerate(taxed_benefits):
            benefit = item.benefit
            add(
                f"benefit-{index}", BENEFITS, benefit.name, year, item.cost,
                tag=TREATMENT_LABELS[benefit.treatment],
                sources=TREATMENT_SOURCES[benefit.treatment],
            )
            if item.note:
                rows[f"benefit-{index}"].note = item.note
            if benefit.treatment == TAXABLE_CASH:
                cash_taxable += item.taxable
            elif benefit.treatment in (BENEFIT_IN_KIND, QUALIFYING_RELOCATION):
                in_kind_taxable += item.taxable

        # 3. UK tax, grossed up: T = UKTax(I + T)
        # I is what the employee takes home under equalisation plus taxable benefits
        hypothetical = swiss_tax.hypothetical_tax(home_pay_chf)
        net_home_pay_chf = home_pay_chf - hypothetical.total - hypothetical.social_security.total
        net_home_pay_gbp = chf_to_gbp(net_home_pay_chf, fx)
        taxable_benefits = cash_taxable + in_kind_taxable
        income_before_tax = net_home_pay_gbp + taxable_benefits

        result = gross_up(income_before_tax, _uk_tax_function(regime, in_kind_taxable))
        uk_tax_on_net = uk_tax.income_tax(income_before_tax)
        uk_tax_at_gross = uk_tax.income_tax(result.gross_income)
        employee_ni = result.tax - uk_tax_at_gross

        add("uk_tax", HOST_TAX, "UK income tax on assignment pay (before tax on tax)", year, uk_tax_on_net,
            sources=["uk_income_tax_rates", "uk_tax_equalisation"])
        add("tax_on_tax", HOST_TAX, "UK income tax on the tax paid by the employer (tax on tax)", year,
            uk_tax_at_gross - uk_tax_on_net, sources=["uk_paye_grossing_up", "uk_tax_equalisation"])

        # Social security depends on whether the posting fits the 24-month limit
        if regime.country == "UK":
            cash_earnings = result.gross_income - in_kind_taxable
            add("ee_ni", HOST_TAX, "Employee Class 1 National Insurance (borne by employer)", year, employee_ni,
                sources=["uk_employer_rates_2026_27"])
            add("er_ni", HOST_TAX, "Employer Class 1 National Insurance", year, uk_tax.employer_ni(cash_earnings),
                sources=["uk_employer_rates_2026_27"])
            add("class_1a", HOST_TAX, "Employer Class 1A National Insurance on benefits in kind", year,
                uk_tax.employer_class_1a(in_kind_taxable), sources=["uk_employer_rates_2026_27"])
        else:
            actual_employee = swiss_tax.employee_social_security(home_pay_chf).total
            actual_employer = swiss_tax.employer_social_security(home_pay_chf).total
            add("ch_ss_ee", HOST_TAX, "Swiss social security, employee share (still paid, AHV/IV/EO and ALV)", year,
                chf_to_gbp(actual_employee, fx), sources=["ch_ahv_contributions", "ch_alv_contributions"])
            add("ch_ss_er", HOST_TAX, "Swiss social security, employer share (AHV/IV/EO and ALV)", year,
                chf_to_gbp(actual_employer, fx), sources=["ch_ahv_contributions", "ch_alv_contributions"])

        # 4. Deductions: what the employee would have paid at home
        add("hypo_tax", DEDUCTIONS, "Hypothetical Swiss income tax (federal, cantonal, communal)", year,
            -chf_to_gbp(hypothetical.total, fx),
            sources=["ch_federal_tariff_2026", "zh_tariff_2026", "zh_cantonal_multiplier", "zh_city_multiplier"])
        add("hypo_ss", DEDUCTIONS, "Hypothetical Swiss social security (AHV/IV/EO and ALV)", year,
            -chf_to_gbp(hypothetical.social_security.total, fx),
            sources=["ch_ahv_contributions", "ch_alv_contributions"])

        working.append(YearWorking(
            hypothetical=hypothetical,
            net_home_pay_gbp=net_home_pay_gbp,
            taxable_benefits_gbp=taxable_benefits,
            grossup=result,
            uk_tax_on_net=uk_tax_on_net,
            uk_tax_at_gross=uk_tax_at_gross,
            employee_ni=employee_ni,
        ))

    ordered = sorted(rows.values(), key=lambda row: SECTIONS.index(row.section))
    return Estimate(data=data, regime=regime, rows=ordered, working=working, assumptions=assumptions(data, regime))


# Plain-language assumptions shown under the results, each with its sources
def assumptions(data, regime):
    items = [
        ("The employer tax-equalises the employee: they bear hypothetical Swiss tax and social "
         "security, and the employer pays all UK tax on their assignment pay and benefits.",
         ["uk_tax_equalisation"]),
        ("The employee is UK tax resident in every assignment year and leaves Swiss tax residence, "
         "so no actual Swiss income tax is due. UK 2026/27 rates (England) are used for every year.",
         ["uk_income_tax_rates"]),
        ("Each assignment year is treated as one full UK tax year (6 April to 5 April).", []),
        (f"Exchange rate is fixed at £1 = CHF {dec(data.chf_per_gbp):.4f} for every year.", []),
        ("Hypothetical Swiss tax is for a single person with no children in the city of Zurich, "
         "without church tax, using 2026 Swiss tariffs. Deductions: employee AHV/IV/EO and ALV, "
         "flat 3% professional expenses (CHF 2,000 to 4,000) and the insurance premium allowance "
         "for a pension fund member (CHF 1,800 federal, CHF 2,900 Zurich). The pension fund (BVG) "
         "contributions themselves are left out.",
         ["ch_federal_deductions_2026", "zh_deductions_2026", "ch_tax_calculator"]),
        (regime.title + ". " + regime.explanation, regime.sources),
        ("Qualifying removal costs (travel, shipping, temporary accommodation) share one £8,000 "
         "exemption for the move; anything above it is a taxable benefit. Cash allowances are "
         "taxable as earnings.",
         ["uk_relocation_exemption", "uk_removal_temporary_accommodation"]),
        ("Housing rented by the employer is a taxable benefit in kind valued at the rent paid.",
         ["uk_accommodation_benefit"]),
        ("UK tax is grossed up by iteration until it changes by less than 1p.", ["uk_paye_grossing_up"]),
        ("Not included: pension (BVG), the Swiss family allowance fund and accident insurance, the "
         "UK Apprenticeship Levy (depends on the UK payroll size), immigration costs (see the "
         "Immigration tab) and any UK tax relief the employee could claim personally.", []),
    ]
    if regime.country == "CH":
        items.append(("Swiss contributions during the assignment are calculated on salary and "
                      "bonus only, as at home.", ["ch_ahv_contributions"]))
    return items
