from datetime import date
from decimal import Decimal

from django.test import SimpleTestCase

from estimator.engine import swiss_tax, uk_tax
from estimator.engine.benefits import (
    ALL_YEARS, BENEFIT_IN_KIND, FIRST_YEAR, MONTHLY, ONE_OFF, QUALIFYING_RELOCATION, TAXABLE_CASH,
    Benefit, apply_uk_treatment,
)
from estimator.engine.estimate import AssignmentInput, build_estimate
from estimator.engine.grossup import GrossUpError, gross_up
from estimator.engine.social_security import determine_regime


class UKIncomeTaxTests(SimpleTestCase):
    def test_personal_allowance_taper(self):
        self.assertEqual(uk_tax.personal_allowance(100_000), 12_570)
        self.assertEqual(uk_tax.personal_allowance(110_000), 7_570)
        self.assertEqual(uk_tax.personal_allowance(125_140), 0)
        self.assertEqual(uk_tax.personal_allowance(200_000), 0)

    def test_income_tax_at_band_edges(self):
        self.assertEqual(uk_tax.income_tax(12_570), 0)
        self.assertEqual(uk_tax.income_tax(50_270), Decimal("7540"))
        self.assertEqual(uk_tax.income_tax(100_000), Decimal("27432"))
        self.assertEqual(uk_tax.income_tax(125_140), Decimal("42516"))
        # Above £125,140 every extra pound is taxed at 45%.
        self.assertEqual(uk_tax.income_tax(200_000), Decimal("42516") + Decimal("74860") * Decimal("0.45"))

    def test_national_insurance(self):
        self.assertEqual(uk_tax.employee_ni(50_270), Decimal("3016.00"))
        self.assertEqual(uk_tax.employee_ni(60_270), Decimal("3216.00"))
        self.assertEqual(uk_tax.employer_ni(50_000), Decimal("6750.00"))


class GrossUpTests(SimpleTestCase):
    def test_flat_rate_matches_closed_form(self):
        # With a flat 20% tax, T = 0.2 (I + T) gives T = I / 4.
        result = gross_up(80, lambda income: income * Decimal("0.2"))
        self.assertAlmostEqual(float(result.tax), 20.0, places=2)

    def test_solution_satisfies_equation_across_bands(self):
        for income in (30_000, 90_000, 110_000, 158_457):
            result = gross_up(income, uk_tax.income_tax)
            self.assertLess(abs(result.tax - uk_tax.income_tax(income + result.tax)), Decimal("0.01"))

    def test_iteration_is_needed(self):
        # One multiplication by the marginal rate would be wrong in the taper zone.
        result = gross_up(90_000, uk_tax.income_tax)
        self.assertGreater(len(result.steps), 2)

    def test_divergent_tax_raises(self):
        with self.assertRaises(GrossUpError):
            gross_up(100, lambda income: income * Decimal("1.5"), max_iterations=20)


class SwissTaxTests(SimpleTestCase):
    def test_federal_tax_matches_estv_table(self):
        # Points published in ESTV Form 58c (2026), single taxpayers.
        self.assertEqual(swiss_tax.federal_tax(60_000), Decimal("671.40"))
        self.assertEqual(swiss_tax.federal_tax(82_100), Decimal("1502.95"))
        self.assertEqual(swiss_tax.federal_tax(148_200), Decimal("6877.55"))
        self.assertEqual(swiss_tax.federal_tax(200_000), Decimal("12903.35"))
        self.assertEqual(swiss_tax.federal_tax(1_000_000), Decimal("115000.00"))
        self.assertEqual(swiss_tax.federal_tax(15_000), 0)

    def test_zurich_simple_tax(self):
        self.assertEqual(swiss_tax.zurich_simple_tax(7_000), 0)
        self.assertEqual(swiss_tax.zurich_simple_tax(12_000), Decimal("100"))
        self.assertEqual(swiss_tax.zurich_simple_tax(16_800), Decimal("244"))

    def test_social_security_caps_alv(self):
        contributions = swiss_tax.employee_social_security(170_000)
        self.assertEqual(contributions.ahv_iv_eo, Decimal("9010"))
        self.assertEqual(contributions.alv, Decimal("1630.20"))

    def test_hypothetical_tax_for_test_case(self):
        result = swiss_tax.hypothetical_tax(170_000)
        self.assertEqual(result.federal_taxable_income, 153_500)
        self.assertEqual(result.federal_tax, Decimal("7460.55"))
        self.assertEqual(result.zurich_taxable_income, 152_400)
        self.assertEqual(result.zurich.simple_tax, Decimal("11389"))
        self.assertEqual(result.total, Decimal("31857.00"))


class SocialSecurityRegimeTests(SimpleTestCase):
    def test_two_year_posting_stays_swiss(self):
        self.assertEqual(determine_regime(24).country, "CH")

    def test_longer_posting_moves_to_uk(self):
        self.assertEqual(determine_regime(25).country, "UK")


class BenefitTests(SimpleTestCase):
    def test_relocation_exemption_is_shared(self):
        benefits = [
            Benefit("Moving", 6000, "GBP", ONE_OFF, FIRST_YEAR, QUALIFYING_RELOCATION),
            Benefit("Temporary housing", 4000, "GBP", ONE_OFF, FIRST_YEAR, QUALIFYING_RELOCATION),
        ]
        taxed, left = apply_uk_treatment(benefits, 0, Decimal("1.10"), Decimal("8000"))
        self.assertEqual([item.taxable for item in taxed], [0, 2000])
        self.assertEqual(left, 0)

    def test_monthly_chf_benefit_is_converted(self):
        benefit = Benefit("Car", 1100, "CHF", MONTHLY, ALL_YEARS, BENEFIT_IN_KIND)
        self.assertEqual(benefit.cost_in_year(1, Decimal("1.10")), Decimal("12000"))


def make_test_case_input(years=2, months=24):
    return AssignmentInput(
        home_country="CH", host_country="UK",
        start_date=date(2026, 4, 6), end_date=date(2028, 4, 5),
        years=years, duration_months=months,
        base_salary_chf=150_000, bonus_chf=20_000, chf_per_gbp=Decimal("1.10"),
        benefits=[
            Benefit("Housing in London", 3000, "GBP", MONTHLY, ALL_YEARS, BENEFIT_IN_KIND),
            Benefit("Relocation allowance", 5000, "CHF", ONE_OFF, FIRST_YEAR, TAXABLE_CASH),
            Benefit("Moving costs", 6000, "GBP", ONE_OFF, FIRST_YEAR, QUALIFYING_RELOCATION),
            Benefit("Temporary housing", 4000, "GBP", ONE_OFF, FIRST_YEAR, QUALIFYING_RELOCATION),
        ],
    )


class EstimateTests(SimpleTestCase):
    def test_test_case_produces_two_years(self):
        estimate = build_estimate(make_test_case_input())
        self.assertEqual(len(estimate.year_totals()), 2)
        self.assertEqual(estimate.regime.country, "CH")
        # Year 1 costs more because of the one-off relocation items.
        first, second = estimate.year_totals()
        self.assertGreater(first, second)
        self.assertEqual(estimate.total, first + second)

    def test_uk_tax_is_grossed_up(self):
        estimate = build_estimate(make_test_case_input())
        for working in estimate.working:
            gross = working.grossup.gross_income
            self.assertLess(abs(working.grossup.tax - uk_tax.income_tax(gross)), Decimal("0.01"))

    def test_test_case_year_one_uk_tax(self):
        # I = net home pay (CHF 127,502.80 / 1.10) + housing 36,000 + cash 4,545.45 + relocation excess 2,000
        # With no personal allowance: T = 0.45 (I + T) - 13,797  =>  T = (0.45 I - 13,797) / 0.55
        estimate = build_estimate(make_test_case_input())
        working = estimate.working[0]
        income = working.grossup.net_income
        expected = (Decimal("0.45") * income - 13_797) / Decimal("0.55")
        self.assertAlmostEqual(float(working.grossup.tax), float(expected), delta=0.05)

    def test_swiss_social_security_nets_out(self):
        estimate = build_estimate(make_test_case_input())
        rows = {row.label: row for row in estimate.rows}
        paid = rows["Swiss social security, employee share (still paid, AHV/IV/EO and ALV)"].total
        deducted = rows["Hypothetical Swiss social security (AHV/IV/EO and ALV)"].total
        self.assertEqual(paid + deducted, 0)

    def test_long_assignment_adds_uk_national_insurance(self):
        estimate = build_estimate(make_test_case_input(years=3, months=36))
        labels = [row.label for row in estimate.rows]
        self.assertIn("Employer Class 1 National Insurance", labels)
        self.assertNotIn("Swiss social security, employer share (AHV/IV/EO and ALV)", labels)

    def test_every_row_except_home_pay_has_a_source(self):
        estimate = build_estimate(make_test_case_input())
        for row in estimate.rows:
            if row.section != "Home pay":
                self.assertTrue(row.sources, row.label)
