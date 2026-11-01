# What a Swiss national needs to work in the UK, what it costs and how long it takes.

import math
from dataclasses import dataclass, field
from datetime import timedelta

from ..rules import immigration as rules
from .money import chf_to_gbp
from .social_security import DETACHMENT_LIMIT_MONTHS

WORK_PERMIT = "Work permit"
BUSINESS_VISIT = "Business visit before the assignment"
PASSPORT = "Passport"
EMPLOYER = "What the employer must do"
CATEGORIES = [WORK_PERMIT, BUSINESS_VISIT, PASSPORT, EMPLOYER]

EMPLOYER_PAYS = "Employer"
EMPLOYEE_PAYS = "Employee (usually reimbursed)"


@dataclass
class ImmigrationInput:
    nationality: str
    start_date: object
    end_date: object
    base_salary_chf: object
    chf_per_gbp: object
    months_with_employer: int
    sponsor_size: str  # "small" or "medium_large"


@dataclass
class Check:
    label: str
    passed: bool
    detail: str
    sources: list


@dataclass
class Requirement:
    category: str
    title: str
    detail: str
    time: str = ""
    cost_gbp: int = 0
    paid_by: str = ""
    sources: list = field(default_factory=list)


@dataclass
class ImmigrationResult:
    route: str
    eligible: bool
    checks: list
    requirements: list
    timeline: dict
    duration_months: int

    def total_cost(self, paid_by=None):
        return sum(r.cost_gbp for r in self.requirements if paid_by is None or r.paid_by == paid_by)


# Whole months from start to end. A period ending the day before an
# anniversary counts as complete, e.g. 6 Apr 2026 to 5 Apr 2028 is 24 months.
def months_between(start, end):
    end = end + timedelta(days=1)
    return (end.year - start.year) * 12 + (end.month - start.month) - (1 if end.day < start.day else 0)


# The surcharge is charged per year, plus half a year for any leftover 6 months or less.
def health_surcharge_years(months):
    full_years, remainder = divmod(months, 12)
    if remainder == 0:
        return full_years
    return full_years + (0.5 if remainder <= 6 else 1)


# Charged for the first 12 months, then for every started 6-month period after that.
def skills_charge(months, sponsor_size):
    extra_periods = max(0, math.ceil((months - 12) / 6))
    return rules.ISC_FIRST_12_MONTHS[sponsor_size] + extra_periods * rules.ISC_EACH_EXTRA_6_MONTHS[sponsor_size]


def assess(data):
    salary_gbp = chf_to_gbp(data.base_salary_chf, data.chf_per_gbp)
    months = months_between(data.start_date, data.end_date)
    years_label = f"{months // 12} years" if months % 12 == 0 else f"{months} months"

    # Eligibility tests for the Senior or Specialist Worker route
    checks = [
        Check(
            "Salary of at least £52,500 (or the going rate for the job, if higher)",
            salary_gbp >= rules.SSW_MIN_SALARY,
            f"Base salary is about £{salary_gbp:,.0f} a year at the exchange rate given. Only guaranteed "
            "basic pay is counted here; check the going rate for the job's occupation code.",
            ["visa_senior_specialist_eligibility"],
        ),
        Check(
            "Worked for the employer outside the UK for at least 12 months",
            data.months_with_employer >= rules.SSW_MIN_MONTHS_WITH_EMPLOYER or salary_gbp >= rules.SSW_NO_TENURE_SALARY,
            (f"{data.months_with_employer} months with the employer."
             + (" Not required anyway, as the salary is £73,900 or more." if salary_gbp >= rules.SSW_NO_TENURE_SALARY else "")),
            ["visa_senior_specialist_eligibility"],
        ),
        Check(
            "Job is on the list of eligible occupations",
            True,
            "Assumed. Confirm the job's 4-digit occupation code against the eligible occupations list "
            "before assigning the certificate of sponsorship.",
            ["visa_senior_specialist_eligibility"],
        ),
        Check(
            "Stay within the maximum for the route",
            months <= 60,
            f"The assignment is {years_label}. The visa lasts for the certificate of sponsorship period "
            "plus 14 days, up to 5 years.",
            ["visa_senior_specialist"],
        ),
    ]
    eligible = all(check.passed for check in checks)

    # Fees depend on how long the visa is for
    visa_fee = rules.SSW_FEE_UP_TO_3_YEARS if months <= 36 else rules.SSW_FEE_OVER_3_YEARS
    surcharge_years = health_surcharge_years(months)
    surcharge = int(rules.IMMIGRATION_HEALTH_SURCHARGE_PER_YEAR * surcharge_years)
    size_label = "small" if data.sponsor_size == "small" else "medium or large"

    requirements = [
        Requirement(
            WORK_PERMIT, "Global Business Mobility: Senior or Specialist Worker visa",
            "The route for multinational companies moving an existing employee to a UK branch or "
            "subsidiary (previously the Intra-company Transfer visa). A visitor cannot do paid or "
            "unpaid work for a UK company, so a work visa is needed for the assignment.",
            sources=["visa_senior_specialist", "sponsor_licence_types", "standard_visitor"],
        ),
        Requirement(
            WORK_PERMIT, "Visa application fee",
            f"Applying from outside the UK for {'up to' if months <= 36 else 'more than'} 3 years. "
            f"The employee must apply within {rules.SSW_APPLY_WITHIN_MONTHS_OF_COS} months of getting "
            "the certificate of sponsorship.",
            time=f"Decision usually within {rules.SSW_DECISION_WEEKS} weeks",
            cost_gbp=visa_fee, paid_by=EMPLOYEE_PAYS,
            sources=["visa_senior_specialist_costs", "visa_senior_specialist", "visa_senior_specialist_eligibility"],
        ),
        Requirement(
            WORK_PERMIT, "Immigration Health Surcharge",
            f"£{rules.IMMIGRATION_HEALTH_SURCHARGE_PER_YEAR:,} per year of the visa, "
            f"{surcharge_years:g} year(s) here. Paid with the visa application.",
            cost_gbp=surcharge, paid_by=EMPLOYEE_PAYS,
            sources=["visa_senior_specialist_costs"],
        ),
        Requirement(
            WORK_PERMIT, "Proof of funds",
            f"At least £{rules.SSW_MAINTENANCE_FUNDS:,} held for 28 days, unless the employer certifies "
            "on the certificate of sponsorship that it will support the employee for the first month.",
            sources=["visa_senior_specialist_costs"],
        ),
        Requirement(
            BUSINESS_VISIT, "No visit visa needed, but an electronic travel authorisation (ETA) is",
            "Swiss nationals can get an ETA instead of a visa. It allows visits of up to 6 months for "
            "permitted business activities such as meetings, conferences, negotiating contracts, site "
            "visits and internal training, as long as the employee is not paid by a UK-based "
            "organisation or client. Any other paid or unpaid work needs a work visa. Once the work "
            "visa is granted, an ETA is no longer needed.",
            time=f"Usually within 1 working day, up to {rules.ETA_DECISION_WORKING_DAYS} working days",
            cost_gbp=rules.ETA_FEE, paid_by=EMPLOYER_PAYS,
            sources=["eta_eligibility", "eta_apply", "business_visit", "standard_visitor", "eta_not_needed"],
        ),
        Requirement(
            PASSPORT, "Valid passport for the visa application",
            "The visa application needs a valid passport or other document showing identity and "
            "nationality. A Swiss passport covers this.",
            sources=["visa_senior_specialist_documents"],
        ),
        Requirement(
            PASSPORT, "Passport for the business visit",
            f"The passport should be valid for the whole visit. The ETA is linked to the passport used "
            f"to apply and lasts {rules.ETA_VALID_YEARS} years or until that passport expires, so a new "
            "passport needs a new ETA.",
            sources=["standard_visitor", "eta_apply"],
        ),
        Requirement(
            PASSPORT, "Link the passport to the eVisa",
            "The work visa is issued as an eVisa (digital immigration status) instead of a physical "
            "document. The employee adds their passport details to their UKVI account to travel with it.",
            sources=["evisa"],
        ),
        Requirement(
            EMPLOYER, "UK subsidiary gets a Worker sponsor licence",
            f"Fee for a {size_label} sponsor. Most applications are decided within "
            f"{rules.SPONSOR_LICENCE_WEEKS} weeks; a priority decision within "
            f"{rules.SPONSOR_PRIORITY_WORKING_DAYS} working days costs £{rules.SPONSOR_PRIORITY_FEE} more "
            "(limited places). The sponsor must pay this fee itself.",
            time=f"Up to {rules.SPONSOR_LICENCE_WEEKS} weeks",
            cost_gbp=rules.SPONSOR_LICENCE_FEE[data.sponsor_size], paid_by=EMPLOYER_PAYS,
            sources=["sponsor_licence_types", "sponsor_licence_apply"],
        ),
        Requirement(
            EMPLOYER, "Assign a certificate of sponsorship",
            "An electronic certificate with details of the UK job. The employer must pay this itself "
            "for Global Business Mobility routes.",
            cost_gbp=rules.COS_FEE, paid_by=EMPLOYER_PAYS,
            sources=["sponsor_cos"],
        ),
        Requirement(
            EMPLOYER, "Pay the Immigration Skills Charge",
            f"For a {size_label} sponsor: £{rules.ISC_FIRST_12_MONTHS[data.sponsor_size]:,} for the first "
            f"12 months and £{rules.ISC_EACH_EXTRA_6_MONTHS[data.sponsor_size]:,} for each further 6 "
            f"months, paid in full when the certificate is assigned ({years_label}). The exemption for "
            "transferred workers applies to EU nationals only, so it does not cover a Swiss national.",
            cost_gbp=skills_charge(months, data.sponsor_size), paid_by=EMPLOYER_PAYS,
            sources=["sponsor_isc"],
        ),
        Requirement(
            EMPLOYER, "Check right to work before the first UK workday",
            "Check the employee's right to work online using the share code from their eVisa, and keep "
            f"a record. Employing someone without a correct check risks a civil penalty of up to "
            f"£{rules.ILLEGAL_WORKING_MAX_PENALTY:,} per worker.",
            sources=["right_to_work", "illegal_working_penalties"],
        ),
    ]
    # Short postings also need proof that Swiss social security still applies
    if months <= DETACHMENT_LIMIT_MONTHS:
        requirements.append(Requirement(
            EMPLOYER, "Get a Swiss certificate of coverage for social security",
            "Apply to the Swiss social security institution so the employee stays in Swiss social "
            "security and no UK National Insurance is due for a posting of up to 2 years.",
            sources=["uk_ss_coming_from_switzerland"],
        ))

    # Licence and visa happen one after the other, so their waits add up
    lead_weeks = rules.SPONSOR_LICENCE_WEEKS + rules.SSW_DECISION_WEEKS
    timeline = [
        {"step": "Apply for the sponsor licence", "weeks": rules.SPONSOR_LICENCE_WEEKS},
        {"step": "Assign the certificate of sponsorship and pay the skills charge", "weeks": 0},
        {"step": "Employee applies for the visa and pays the health surcharge", "weeks": rules.SSW_DECISION_WEEKS},
        {"step": "Right to work check, then the employee starts in the UK", "weeks": 0},
    ]
    latest_start = data.start_date - timedelta(weeks=lead_weeks)

    return ImmigrationResult(
        route="Senior or Specialist Worker visa (Global Business Mobility)",
        eligible=eligible,
        checks=checks,
        requirements=requirements,
        timeline={"steps": timeline, "total_weeks": lead_weeks, "start_by": latest_start},
        duration_months=months,
    )
