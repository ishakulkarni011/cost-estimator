# Turns engine results into JSON for the front end.

from datetime import timedelta

from .engine.estimate import SECTION_DESCRIPTIONS, SECTIONS
from .engine.immigration import CATEGORIES, EMPLOYEE_PAYS, EMPLOYER_PAYS
from .engine.money import gbp_to_chf, round_money
from .engine.uk_tax import income_tax_breakdown
from .forms import add_years
from .rules.sources import get_source


def money(value):
    return float(round_money(value))


def sources(keys):
    return [{"title": get_source(key).title, "url": get_source(key).url} for key in keys]


# Every amount is sent in both GBP and CHF so the page can switch without a new request
def both_currencies(amounts, total, fx):
    return {
        "gbp": [money(a) for a in amounts],
        "gbp_total": money(total),
        "chf": [money(gbp_to_chf(a, fx)) for a in amounts],
        "chf_total": money(gbp_to_chf(total, fx)),
    }


def format_date(day):
    return f"{day.day} {day:%b %Y}"


# Column headings, e.g. "Year 1" and "6 Apr 2026 to 5 Apr 2027"
def year_periods(data):
    periods = []
    for year in range(data.years):
        start = add_years(data.start_date, year)
        end = add_years(data.start_date, year + 1) - timedelta(days=1)
        periods.append({"label": f"Year {year + 1}", "period": f"{format_date(start)} to {format_date(end)}"})
    return periods


def serialize_estimate(estimate):
    data = estimate.data
    fx = data.chf_per_gbp

    sections = []
    for name in SECTIONS:
        rows = estimate.section_rows(name)
        if not rows:
            continue
        subtotal = [sum(row.amounts[y] for row in rows) for y in range(data.years)]
        sections.append({
            "name": name,
            "description": SECTION_DESCRIPTIONS[name],
            "rows": [
                {
                    "label": row.label,
                    "tag": row.tag,
                    "note": row.note,
                    "sources": sources(row.sources),
                    **both_currencies(row.amounts, row.total, fx),
                }
                for row in rows
            ],
            "subtotal": both_currencies(subtotal, sum(subtotal), fx),
        })

    per_year_multiple, overall_multiple = estimate.multiples()
    return {
        "chf_per_gbp": float(fx),
        "years": year_periods(data),
        "sections": sections,
        "total": both_currencies(estimate.year_totals(), estimate.total, fx),
        "multiple_of_home_pay": [round(float(m), 2) for m in per_year_multiple],
        "multiple_of_home_pay_total": round(float(overall_multiple), 2),
        "social_security": {
            "country": estimate.regime.country,
            "title": estimate.regime.title,
            "explanation": estimate.regime.explanation,
            "sources": sources(estimate.regime.sources),
        },
        "assumptions": [{"text": text, "sources": sources(keys)} for text, keys in estimate.assumptions],
        "working": [serialize_working(year, working) for year, working in enumerate(estimate.working, start=1)],
    }


# The step-by-step figures behind one year, for the Working section
def serialize_working(year, working):
    hypo = working.hypothetical
    result = working.grossup
    bands = income_tax_breakdown(result.gross_income)
    return {
        "year": year,
        "hypothetical_chf": {
            "gross_salary": money(hypo.gross_salary),
            "social_security": money(hypo.social_security.total),
            "federal_professional_expenses": money(hypo.federal_professional_expenses),
            "federal_insurance_deduction": money(hypo.federal_insurance_deduction),
            "federal_taxable_income": money(hypo.federal_taxable_income),
            "federal_tax": money(hypo.federal_tax),
            "zurich_professional_expenses": money(hypo.zurich_professional_expenses),
            "zurich_insurance_deduction": money(hypo.zurich_insurance_deduction),
            "zurich_taxable_income": money(hypo.zurich_taxable_income),
            "zurich_simple_tax": money(hypo.zurich.simple_tax),
            "zurich_cantonal_tax": money(hypo.zurich.cantonal),
            "zurich_communal_tax": money(hypo.zurich.communal),
            "zurich_personal_tax": money(hypo.zurich.personal_tax),
            "total_tax": money(hypo.total),
        },
        "net_home_pay_gbp": money(working.net_home_pay_gbp),
        "taxable_benefits_gbp": money(working.taxable_benefits_gbp),
        "income_before_tax_gbp": money(result.net_income),
        "grossup_steps": [
            {"iteration": s.iteration, "gross_income": money(s.gross_income), "tax": money(s.tax)}
            for s in result.steps
        ],
        "uk_tax_gbp": money(result.tax),
        "gross_taxable_income_gbp": money(result.gross_income),
        "uk_bands": {
            "personal_allowance": money(bands.personal_allowance),
            "taxable_income": money(bands.taxable_income),
            "bands": [
                {"name": band.name, "rate": float(band.rate), "income": money(band.income_in_band), "tax": money(band.tax)}
                for band in bands.bands
            ],
        },
    }


def serialize_immigration(result):
    return {
        "route": result.route,
        "eligible": result.eligible,
        "duration_months": result.duration_months,
        "checks": [
            {"label": c.label, "passed": c.passed, "detail": c.detail, "sources": sources(c.sources)}
            for c in result.checks
        ],
        "categories": [
            {
                "name": category,
                "requirements": [
                    {
                        "title": r.title,
                        "detail": r.detail,
                        "time": r.time,
                        "cost_gbp": r.cost_gbp,
                        "paid_by": r.paid_by,
                        "sources": sources(r.sources),
                    }
                    for r in result.requirements
                    if r.category == category
                ],
            }
            for category in CATEGORIES
        ],
        "costs": {
            "employer": result.total_cost(EMPLOYER_PAYS),
            "employee": result.total_cost(EMPLOYEE_PAYS),
            "total": result.total_cost(),
        },
        "timeline": {
            "steps": result.timeline["steps"],
            "total_weeks": result.timeline["total_weeks"],
            "start_by": format_date(result.timeline["start_by"]),
        },
    }
