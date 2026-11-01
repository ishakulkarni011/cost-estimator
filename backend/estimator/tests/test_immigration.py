import json
from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from estimator.engine.immigration import ImmigrationInput, assess, health_surcharge_years, months_between, skills_charge

TEST_CASE = {
    "nationality": "CH",
    "host_country": "UK",
    "start_date": "2026-04-06",
    "end_date": "2028-04-05",
    "base_salary_chf": "150000",
    "chf_per_gbp": "1.10",
    "months_with_employer": "36",
    "sponsor_size": "medium_large",
}


class ImmigrationRuleTests(SimpleTestCase):
    def test_duration_in_months(self):
        self.assertEqual(months_between(date(2026, 4, 6), date(2028, 4, 5)), 24)
        self.assertEqual(months_between(date(2026, 4, 6), date(2026, 10, 5)), 6)

    def test_health_surcharge_years(self):
        self.assertEqual(health_surcharge_years(24), 2)
        self.assertEqual(health_surcharge_years(30), 2.5)
        self.assertEqual(health_surcharge_years(31), 3)

    def test_skills_charge(self):
        self.assertEqual(skills_charge(24, "medium_large"), 2640)
        self.assertEqual(skills_charge(24, "small"), 960)
        self.assertEqual(skills_charge(12, "small"), 480)

    def test_low_salary_short_tenure_is_not_eligible(self):
        result = assess(ImmigrationInput("CH", date(2026, 4, 6), date(2028, 4, 5), 50_000, 1.10, 6, "small"))
        self.assertFalse(result.eligible)


class ImmigrationApiTests(TestCase):
    url = reverse("estimator:immigration_api")

    def post(self, payload):
        return self.client.post(self.url, json.dumps(payload), content_type="application/json")

    def test_test_case_covers_work_permit_business_visit_and_passport(self):
        response = self.post(TEST_CASE)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["eligible"])
        categories = {c["name"]: c["requirements"] for c in body["categories"]}
        for name in ("Work permit", "Business visit before the assignment", "Passport", "What the employer must do"):
            self.assertTrue(categories[name], name)
        for requirements in categories.values():
            for requirement in requirements:
                self.assertTrue(requirement["sources"], requirement["title"])
        # Visa 819 + surcharge 2,070 + ETA 20 + licence 1,682 + certificate 525 + skills charge 2,640
        self.assertEqual(body["costs"]["total"], 7756)

    def test_missing_field(self):
        payload = {k: v for k, v in TEST_CASE.items() if k != "months_with_employer"}
        response = self.post(payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"]["months_with_employer"], ["Months with the employer is required."])

    def test_unsupported_nationality(self):
        response = self.post({**TEST_CASE, "nationality": "US"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Swiss nationals", response.json()["errors"]["nationality"][0])
