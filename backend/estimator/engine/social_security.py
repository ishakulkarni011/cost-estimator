# Decides which country's social security applies during the assignment.

from dataclasses import dataclass

# Under Art. 14 of the UK-Switzerland Convention a worker sent to the other
# country stays in the home system if the posting is expected to last no
# more than 24 months and they are not replacing another posted worker.
DETACHMENT_LIMIT_MONTHS = 24


@dataclass
class SocialSecurityRegime:
    country: str  # "CH" or "UK"
    title: str
    explanation: str
    sources: list


def determine_regime(duration_months):
    if duration_months <= DETACHMENT_LIMIT_MONTHS:
        return SocialSecurityRegime(
            country="CH",
            title="Swiss social security continues (AHV/IV/EO and ALV); no UK National Insurance",
            explanation=(
                f"The assignment lasts {duration_months} months, within the "
                f"{DETACHMENT_LIMIT_MONTHS}-month limit for detached workers in the UK-Switzerland "
                "Convention on Social Security. The Swiss employer applies for a certificate of "
                "coverage, so neither the employee nor the employer pays UK Class 1 or Class 1A "
                "National Insurance. Swiss contributions carry on as if the employee were at home."
            ),
            sources=["uk_swiss_ss_convention", "uk_ss_coming_from_switzerland"],
        )
    return SocialSecurityRegime(
        country="UK",
        title="UK National Insurance applies from day one",
        explanation=(
            f"The assignment lasts {duration_months} months, more than the "
            f"{DETACHMENT_LIMIT_MONTHS}-month limit for detached workers, so the employee "
            "moves into the UK system: employee and employer Class 1 and Class 1A National "
            "Insurance are due, and Swiss contributions stop."
        ),
        sources=["uk_swiss_ss_convention", "uk_ss_coming_from_switzerland", "uk_employer_rates_2026_27"],
    )
