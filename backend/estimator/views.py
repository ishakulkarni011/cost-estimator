import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .engine.benefits import Benefit
from .engine.estimate import AssignmentInput, build_estimate
from .engine.grossup import GrossUpError
from .engine.immigration import ImmigrationInput, assess
from .forms import AssignmentForm, BenefitForm, ImmigrationForm, form_errors
from .serializers import serialize_estimate, serialize_immigration


# The single page; everything else on it is loaded through the API
def index(request):
    return render(request, "estimator/index.html")


def error_response(message, errors=None, status=400):
    return JsonResponse({"error": message, "errors": errors or {}}, status=status)


# Returns the request body as a dict, or None if it is not a JSON object.
def parse_json(request):
    try:
        payload = json.loads(request.body or b"")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@require_POST
def estimate_api(request):
    payload = parse_json(request)
    if payload is None:
        return error_response("The request body must be a JSON object.")

    form = AssignmentForm(payload)
    raw_benefits = payload.get("benefits", [])
    if not isinstance(raw_benefits, list):
        return error_response("Benefits must be a list.", {"benefits": ["Benefits must be a list."]})

    # Validate every benefit row too, so all errors come back in one response
    benefit_forms = [BenefitForm(item if isinstance(item, dict) else {}) for item in raw_benefits]
    form_ok = form.is_valid()
    benefits_ok = all([bf.is_valid() for bf in benefit_forms])
    if not (form_ok and benefits_ok):
        errors = form_errors(form)
        for index, bf in enumerate(benefit_forms):
            for field, messages in form_errors(bf).items():
                errors[f"benefits.{index}.{field}"] = [f"Benefit {index + 1}: {m}" for m in messages]
        return error_response("Some inputs need correcting.", errors)

    # Inputs are valid, hand them to the calculation engine
    data = form.cleaned_data
    assignment = AssignmentInput(
        home_country=data["home_country"],
        host_country=data["host_country"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        years=data["years"],
        duration_months=data["duration_months"],
        base_salary_chf=data["base_salary_chf"],
        bonus_chf=data["bonus_chf"],
        chf_per_gbp=data["chf_per_gbp"],
        benefits=[Benefit(**bf.cleaned_data) for bf in benefit_forms],
    )
    try:
        estimate = build_estimate(assignment)
    except GrossUpError as exc:
        return error_response(str(exc), status=422)
    return JsonResponse(serialize_estimate(estimate))


@require_POST
def immigration_api(request):
    payload = parse_json(request)
    if payload is None:
        return error_response("The request body must be a JSON object.")

    form = ImmigrationForm(payload)
    if not form.is_valid():
        return error_response("Some inputs need correcting.", form_errors(form))

    data = form.cleaned_data
    result = assess(ImmigrationInput(
        nationality=data["nationality"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        base_salary_chf=data["base_salary_chf"],
        chf_per_gbp=data["chf_per_gbp"],
        months_with_employer=data["months_with_employer"],
        sponsor_size=data["sponsor_size"],
    ))
    return JsonResponse(serialize_immigration(result))
