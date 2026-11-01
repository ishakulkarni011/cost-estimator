# Validation for the cost estimate and immigration inputs.
# The API takes JSON, but it goes through Django forms so every missing or
# malformed field comes back with a readable message.

from datetime import timedelta
from decimal import Decimal

from django import forms

from .engine import benefits as b

HOME_COUNTRIES = [("CH", "Switzerland")]
HOST_COUNTRIES = [("UK", "United Kingdom")]
HOME_CITIES = [("zurich", "Zurich (city)")]
FAMILY_STATUSES = [("single", "Single, no children")]
NATIONALITIES = [("CH", "Swiss")]
SPONSOR_SIZES = [
    ("medium_large", "Medium or large company"),
    ("small", "Small company or charity"),
]
MAX_YEARS = 5


def add_years(day, years):
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # 29 February
        return day.replace(year=day.year + years, day=28)


class AssignmentForm(forms.Form):
    home_country = forms.ChoiceField(choices=HOME_COUNTRIES, error_messages={
        "invalid_choice": "Only Switzerland is supported as the home country for now.",
    })
    host_country = forms.ChoiceField(choices=HOST_COUNTRIES, error_messages={
        "invalid_choice": "Only the United Kingdom is supported as the host country for now.",
    })
    home_city = forms.ChoiceField(choices=HOME_CITIES, initial="zurich")
    family_status = forms.ChoiceField(choices=FAMILY_STATUSES, initial="single")
    start_date = forms.DateField(label="Start date", error_messages={"invalid": "Enter the start date as YYYY-MM-DD."})
    end_date = forms.DateField(label="End date", error_messages={"invalid": "Enter the end date as YYYY-MM-DD."})
    base_salary_chf = forms.DecimalField(
        label="Base salary", min_value=0, max_value=100_000_000, decimal_places=2,
        error_messages={"invalid": "Base salary must be a number, for example 150000."},
    )
    bonus_chf = forms.DecimalField(
        label="Bonus", min_value=0, max_value=100_000_000, decimal_places=2, required=False,
        error_messages={"invalid": "Bonus must be a number, for example 20000."},
    )
    chf_per_gbp = forms.DecimalField(
        label="Exchange rate", min_value=Decimal("0.01"), max_value=100, decimal_places=6,
        error_messages={"invalid": "Exchange rate must be a number, for example 1.10."},
    )

    def clean_bonus_chf(self):
        return self.cleaned_data.get("bonus_chf") or Decimal("0")

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end:
            if end <= start:
                self.add_error("end_date", "The end date must be after the start date.")
            else:
                # Only whole years are supported, ending the day before an anniversary
                years = round((end - start).days / 365.25)
                if years < 1 or years > MAX_YEARS or add_years(start, years) - timedelta(days=1) != end:
                    self.add_error(
                        "end_date",
                        "The tool works in whole assignment years (1 to 5). The end date should be the "
                        "day before an anniversary of the start date, e.g. 2026-04-06 to 2028-04-05.",
                    )
                else:
                    cleaned["years"] = years
                    cleaned["duration_months"] = years * 12
        return cleaned


class BenefitForm(forms.Form):
    name = forms.CharField(max_length=80, error_messages={"required": "Give the benefit a name."})
    amount = forms.DecimalField(
        label="Amount", min_value=0, max_value=100_000_000, decimal_places=2,
        error_messages={"invalid": "Amount must be a number, for example 3000."},
    )
    currency = forms.ChoiceField(choices=[("GBP", "GBP"), ("CHF", "CHF")])
    frequency = forms.ChoiceField(choices=[
        (b.MONTHLY, "Per month"), (b.ANNUAL, "Per year"), (b.ONE_OFF, "One-off"),
    ])
    years = forms.ChoiceField(choices=[(b.ALL_YEARS, "Every year"), (b.FIRST_YEAR, "Year 1 only")])
    treatment = forms.ChoiceField(choices=list(b.TREATMENT_LABELS.items()))


# Reuses the date, salary and exchange rate fields from the cost form
class ImmigrationForm(forms.Form):
    nationality = forms.ChoiceField(choices=NATIONALITIES, error_messages={
        "invalid_choice": "Only Swiss nationals are covered for now.",
    })
    host_country = AssignmentForm.base_fields["host_country"]
    start_date = AssignmentForm.base_fields["start_date"]
    end_date = AssignmentForm.base_fields["end_date"]
    base_salary_chf = AssignmentForm.base_fields["base_salary_chf"]
    chf_per_gbp = AssignmentForm.base_fields["chf_per_gbp"]
    months_with_employer = forms.IntegerField(
        label="Months with the employer", min_value=0, max_value=600,
        error_messages={"invalid": "Months with the employer must be a whole number, for example 36."},
    )
    sponsor_size = forms.ChoiceField(choices=SPONSOR_SIZES)

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if start and end and end <= start:
            self.add_error("end_date", "The end date must be after the start date.")
        return cleaned


# Flattens Django form errors into {field: [messages]} with friendly field names.
def form_errors(form):
    errors = {}
    for field, messages in form.errors.items():
        if field != "__all__" and field in form.fields:
            label = form.fields[field].label or field.replace("_", " ").capitalize()
            messages = [m if m != "This field is required." else f"{label} is required." for m in messages]
        errors[field] = list(messages)
    return errors
