# Official pages that every tax rule and immigration requirement links back to.
# Rules refer to these by key, so the UI can link each figure to its source.

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    title: str
    url: str


SOURCES = {
    # UK tax
    "uk_income_tax_rates": Source(
        "GOV.UK: Income Tax rates and Personal Allowances",
        "https://www.gov.uk/income-tax-rates",
    ),
    "uk_employer_rates_2026_27": Source(
        "GOV.UK: Rates and thresholds for employers 2026 to 2027",
        "https://www.gov.uk/guidance/rates-and-thresholds-for-employers-2026-to-2027",
    ),
    "uk_tax_equalisation": Source(
        "HMRC: Tax equalisation (HS212)",
        "https://www.gov.uk/government/publications/tax-equalisation-hs212-self-assessment-helpsheet",
    ),
    "uk_paye_grossing_up": Source(
        "HMRC PAYE Manual PAYE72028: how to gross up",
        "https://www.gov.uk/hmrc-internal-manuals/paye-manual/paye72028",
    ),
    "uk_accommodation_benefit": Source(
        "GOV.UK: Expenses and benefits - accommodation",
        "https://www.gov.uk/expenses-and-benefits-accommodation/print",
    ),
    "uk_relocation_exemption": Source(
        "GOV.UK: Expenses and benefits - relocation costs (£8,000 exemption)",
        "https://www.gov.uk/expenses-and-benefits-relocation/print",
    ),
    "uk_removal_temporary_accommodation": Source(
        "HMRC Employment Income Manual EIM03100: removal costs, incl. temporary living accommodation",
        "https://www.gov.uk/hmrc-internal-manuals/employment-income-manual/eim03100",
    ),
    # Social security between the UK and Switzerland
    "uk_ss_coming_from_switzerland": Source(
        "GOV.UK: Social security contributions for workers coming to the UK from the EU or Switzerland",
        "https://www.gov.uk/guidance/social-security-contributions-for-workers-coming-to-the-uk-from-the-eea-or-switzerland",
    ),
    "uk_swiss_ss_convention": Source(
        "UK-Switzerland Convention on Social Security Coordination (Art. 14, detached workers)",
        "https://assets.publishing.service.gov.uk/media/61543391d3bf7f718a54c14c/CS_Swiss_4.2021_UK_Swiss_Social_Security_Coordination.pdf",
    ),
    # Swiss social security
    "ch_ahv_contributions": Source(
        "AHV/IV information centre: leaflet 2.01, salary contributions to AHV/IV/EO (1 Jan 2026)",
        "https://www.ahv-iv.ch/p/2.01.d",
    ),
    "ch_alv_contributions": Source(
        "AHV/IV information centre: leaflet 2.08, unemployment insurance contributions",
        "https://www.ahv-iv.ch/p/2.08.d",
    ),
    # Swiss income tax
    "ch_federal_tariff_2026": Source(
        "ESTV: Federal income tax tariffs 2026 (Form 58c)",
        "https://www.estv.admin.ch/dam/de/sd-web/gnde9CmEsalK/dbst-tairfe-58c-2026-dfi.pdf",
    ),
    "ch_federal_deductions_2026": Source(
        "ESTV: Circular 2-215, deductions and tariffs for tax year 2026",
        "https://www.estv.admin.ch/dam/de/sd-web/vFK3ntWLQ4s4/2-215-D-2025-d.pdf",
    ),
    "zh_tariff_2026": Source(
        "Canton of Zurich: Ordinance on cold progression from 1 Jan 2026 (tariff § 35 StG)",
        "https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung/zhlex-os/erlass-631_1-80-273.html",
    ),
    "zh_deductions_2026": Source(
        "Canton of Zurich: Guide to the 2026 tax return (deductions)",
        "https://www.zh.ch/content/dam/zhweb/bilder-dokumente/themen/steuern-finanzen/steuern/natuerlichepersonen/2026/est-wegleitungen-uj/305%20Wegleitung%20ZH%202026%20UJ%20bf.pdf",
    ),
    "zh_cantonal_multiplier": Source(
        "Canton of Zurich: current tax multipliers (cantonal 95% for 2026)",
        "https://www.zh.ch/de/steuern-finanzen/steuern/steuerstatistiken/aktuelle-gemeinde-steuerfuesse.html",
    ),
    "zh_city_multiplier": Source(
        "City of Zurich: tax calculation and multiplier (119%)",
        "https://www.stadt-zuerich.ch/de/lebenslagen/steuern/natuerliche-personen/steuerberechnung.html",
    ),
    "zh_personal_tax": Source(
        "Canton of Zurich tax manual ZStB 173.1: personal tax of CHF 24",
        "https://www.zh.ch/de/steuern-finanzen/steuern/treuhaender/steuerbuch/steuerbuch-definition/zstb-173-1.html",
    ),
    "ch_tax_calculator": Source(
        "ESTV: Swiss tax calculator (to check the hypothetical tax)",
        "https://swisstaxcalculator.estv.admin.ch/",
    ),
    # UK immigration
    "visa_senior_specialist": Source(
        "GOV.UK: Senior or Specialist Worker visa (Global Business Mobility)",
        "https://www.gov.uk/senior-specialist-worker-visa",
    ),
    "visa_senior_specialist_eligibility": Source(
        "GOV.UK: Senior or Specialist Worker visa - eligibility",
        "https://www.gov.uk/senior-specialist-worker-visa/eligibility",
    ),
    "visa_senior_specialist_costs": Source(
        "GOV.UK: Senior or Specialist Worker visa - how much it costs",
        "https://www.gov.uk/senior-specialist-worker-visa/how-much-it-costs",
    ),
    "visa_senior_specialist_documents": Source(
        "GOV.UK: Senior or Specialist Worker visa - documents you need",
        "https://www.gov.uk/senior-specialist-worker-visa/documents-you-need-to-apply",
    ),
    "sponsor_licence_types": Source(
        "GOV.UK: UK visa sponsorship for employers - types of licence",
        "https://www.gov.uk/uk-visa-sponsorship-employers/types-of-licence",
    ),
    "sponsor_licence_apply": Source(
        "GOV.UK: UK visa sponsorship for employers - apply for your licence",
        "https://www.gov.uk/uk-visa-sponsorship-employers/apply-for-your-licence",
    ),
    "sponsor_cos": Source(
        "GOV.UK: UK visa sponsorship for employers - certificates of sponsorship",
        "https://www.gov.uk/uk-visa-sponsorship-employers/certificates-of-sponsorship",
    ),
    "sponsor_isc": Source(
        "GOV.UK: UK visa sponsorship for employers - immigration skills charge",
        "https://www.gov.uk/uk-visa-sponsorship-employers/immigration-skills-charge",
    ),
    "right_to_work": Source(
        "GOV.UK: Check a job applicant's right to work",
        "https://www.gov.uk/check-job-applicant-right-to-work",
    ),
    "illegal_working_penalties": Source(
        "GOV.UK: Penalties for employing illegal workers",
        "https://www.gov.uk/penalties-for-employing-illegal-workers",
    ),
    "eta_eligibility": Source(
        "GOV.UK: Check if you can get an electronic travel authorisation (ETA)",
        "https://www.gov.uk/guidance/check-when-you-can-get-an-electronic-travel-authorisation-eta",
    ),
    "eta_apply": Source(
        "GOV.UK: Apply for an electronic travel authorisation (ETA)",
        "https://www.gov.uk/eta/apply",
    ),
    "eta_not_needed": Source(
        "GOV.UK: When you do not need an ETA",
        "https://www.gov.uk/eta/when-not-need-eta",
    ),
    "business_visit": Source(
        "GOV.UK: Visit the UK on business - permitted activities",
        "https://www.gov.uk/standard-visitor/visit-on-business",
    ),
    "standard_visitor": Source(
        "GOV.UK: Visit the UK as a Standard Visitor",
        "https://www.gov.uk/standard-visitor",
    ),
    "evisa": Source(
        "GOV.UK: Online immigration status (eVisa)",
        "https://www.gov.uk/evisa",
    ),
}


def get_source(key):
    return SOURCES[key]
