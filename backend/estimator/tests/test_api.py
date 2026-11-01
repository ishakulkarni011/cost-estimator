import json

from django.test import TestCase
from django.urls import reverse

TEST_CASE = {
    "home_country": "CH",
    "host_country": "UK",
    "home_city": "zurich",
    "family_status": "single",
    "start_date": "2026-04-06",
    "end_date": "2028-04-05",
    "base_salary_chf": "150000",
    "bonus_chf": "20000",
    "chf_per_gbp": "1.10",
    "benefits": [
        {"name": "Housing in London", "amount": "3000", "currency": "GBP", "frequency": "monthly",
         "years": "all", "treatment": "benefit_in_kind"},
        {"name": "Relocation allowance", "amount": "5000", "currency": "CHF", "frequency": "one_off",
         "years": "first", "treatment": "taxable_cash"},
        {"name": "Moving costs (flights, shipping)", "amount": "6000", "currency": "GBP", "frequency": "one_off",
         "years": "first", "treatment": "qualifying_relocation"},
        {"name": "Temporary housing", "amount": "4000", "currency": "GBP", "frequency": "one_off",
         "years": "first", "treatment": "qualifying_relocation"},
    ],
}


class EstimateApiTests(TestCase):
    url = reverse("estimator:estimate_api")

    def post(self, payload):
        body = payload if isinstance(payload, (str, bytes)) else json.dumps(payload)
        return self.client.post(self.url, body, content_type="application/json")

    def test_test_case_returns_two_year_table(self):
        response = self.post(TEST_CASE)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual([y["label"] for y in body["years"]], ["Year 1", "Year 2"])
        self.assertEqual(
            [s["name"] for s in body["sections"]],
            ["Home pay", "Assignment benefits", "Host tax and charges paid by the employer", "Deductions"],
        )
        self.assertEqual(len(body["total"]["gbp"]), 2)
        self.assertEqual(body["social_security"]["country"], "CH")
        self.assertTrue(body["assumptions"])

    def test_every_rule_row_links_to_a_source(self):
        body = self.post(TEST_CASE).json()
        for section in body["sections"][1:]:
            for row in section["rows"]:
                self.assertTrue(row["sources"], row["label"])
                for source in row["sources"]:
                    self.assertTrue(source["url"].startswith("https://"))

    def test_missing_salary_gives_readable_error(self):
        payload = {k: v for k, v in TEST_CASE.items() if k != "base_salary_chf"}
        response = self.post(payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"]["base_salary_chf"], ["Base salary is required."])

    def test_malformed_number_gives_readable_error(self):
        response = self.post({**TEST_CASE, "chf_per_gbp": "one point one"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Exchange rate must be a number", response.json()["errors"]["chf_per_gbp"][0])

    def test_negative_salary_is_rejected(self):
        response = self.post({**TEST_CASE, "base_salary_chf": "-5"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("base_salary_chf", response.json()["errors"])

    def test_unsupported_country(self):
        response = self.post({**TEST_CASE, "host_country": "FR"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("United Kingdom", response.json()["errors"]["host_country"][0])

    def test_end_date_before_start(self):
        response = self.post({**TEST_CASE, "end_date": "2025-01-01"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("after the start date", response.json()["errors"]["end_date"][0])

    def test_partial_year_is_explained(self):
        response = self.post({**TEST_CASE, "end_date": "2027-10-01"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("whole assignment years", response.json()["errors"]["end_date"][0])

    def test_bad_benefit_reports_which_one(self):
        benefits = [*TEST_CASE["benefits"], {"name": "Car", "amount": "abc", "currency": "GBP",
                                             "frequency": "monthly", "years": "all", "treatment": "benefit_in_kind"}]
        response = self.post({**TEST_CASE, "benefits": benefits})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Benefit 5", response.json()["errors"]["benefits.4.amount"][0])

    def test_invalid_json(self):
        response = self.post("{not json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "The request body must be a JSON object.")

    def test_get_is_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
