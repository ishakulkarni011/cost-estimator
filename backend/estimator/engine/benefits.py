# Assignment benefits and how the UK taxes them.

from dataclasses import dataclass

from ..rules import uk as uk_rules
from .money import ZERO, chf_to_gbp, dec

TAXABLE_CASH = "taxable_cash"
BENEFIT_IN_KIND = "benefit_in_kind"
QUALIFYING_RELOCATION = "qualifying_relocation"
NOT_TAXABLE = "not_taxable"

TREATMENT_LABELS = {
    TAXABLE_CASH: "Taxable cash",
    BENEFIT_IN_KIND: "Taxable benefit in kind",
    QUALIFYING_RELOCATION: "Qualifying relocation cost (exempt up to £8,000)",
    NOT_TAXABLE: "Not taxable in the UK",
}

TREATMENT_SOURCES = {
    TAXABLE_CASH: ["uk_relocation_exemption"],
    BENEFIT_IN_KIND: ["uk_accommodation_benefit"],
    QUALIFYING_RELOCATION: ["uk_relocation_exemption", "uk_removal_temporary_accommodation"],
    NOT_TAXABLE: [],
}

MONTHLY = "monthly"
ANNUAL = "annual"
ONE_OFF = "one_off"

ALL_YEARS = "all"
FIRST_YEAR = "first"


@dataclass
class Benefit:
    name: str
    amount: object
    currency: str      # "GBP" or "CHF"
    frequency: str     # MONTHLY, ANNUAL or ONE_OFF
    years: str         # ALL_YEARS or FIRST_YEAR
    treatment: str

    # Cost to the employer in GBP for one assignment year (0 is the first year).
    def cost_in_year(self, year_index, chf_per_gbp):
        # One-off and first-year-only items cost nothing after year one
        if self.frequency == ONE_OFF or self.years == FIRST_YEAR:
            if year_index != 0:
                return ZERO
        amount = dec(self.amount)
        if self.frequency == MONTHLY:
            amount *= 12
        if self.currency == "CHF":
            amount = chf_to_gbp(amount, chf_per_gbp)
        return amount


@dataclass
class TaxedBenefit:
    benefit: Benefit
    cost: object
    taxable: object
    note: str = ""


# Works out the UK taxable amount of each benefit for one year.
# The £8,000 relocation exemption covers the whole move, so any part not used
# this year carries over. Returns the taxed benefits and the exemption left.
def apply_uk_treatment(benefits, year_index, chf_per_gbp, relocation_exemption_left):
    taxed = []
    for benefit in benefits:
        cost = benefit.cost_in_year(year_index, chf_per_gbp)
        if benefit.treatment in (TAXABLE_CASH, BENEFIT_IN_KIND):
            taxed.append(TaxedBenefit(benefit, cost, cost))
        elif benefit.treatment == QUALIFYING_RELOCATION:
            # Use up as much of the shared exemption as this cost allows
            exempt = min(cost, relocation_exemption_left)
            relocation_exemption_left -= exempt
            note = f"£{exempt:,.0f} exempt" if cost else ""
            if cost - exempt > 0:
                note += f", £{cost - exempt:,.0f} over the £{uk_rules.RELOCATION_EXEMPTION:,} limit is taxable"
            taxed.append(TaxedBenefit(benefit, cost, cost - exempt, note))
        else:
            taxed.append(TaxedBenefit(benefit, cost, ZERO))
    return taxed, relocation_exemption_left
