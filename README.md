# Global Mobility Planner

A small Django tool that tells a company what it will cost, and how long it will take, to send an
employee to work in another country. It is built around one case: an employee sent from
**Zurich, Switzerland to London, UK for two years**.

The page has three tabs, listed in a sidebar on the left:

- **Cost estimate:** the yearly cost to the employer under tax equalisation, with the UK tax
  grossed up by iteration (`T = UKTax(I + T)`), hypothetical Swiss tax and social security.
- **Immigration:** the work visa, the business visit before the assignment, passport rules and
  what the employer must do, with timings and costs.
- **Sources:** the official page behind every rate, fee and rule used in the results.

Video walkthrough: <https://www.loom.com/share/0fd06543c611402ca9da91c8a111720a>

> This is an exercise, not tax or immigration advice.

## Install and run

You need **Python 3.10 or newer** and `git`. Nothing else: no database setup, no Node, no API keys.

```bash
git clone https://github.com/ishakulkarni011/cost-estimator.git
cd cost-estimator

python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
python manage.py runserver
```

On Windows, activate the environment with `.venv\Scripts\activate` instead of the `source` line.

Open <http://127.0.0.1:8000/> and press **Fill in the worked example** to see a full cost estimate.
Press `Ctrl+C` in the terminal to stop the server.

No secret key is stored in the repository. For local use the app generates a random one at start-up;
for a real deployment set `DJANGO_SECRET_KEY` and `DJANGO_DEBUG=0` in the environment.

## Using the app

1. **Fill in the form**, or press **Fill in the worked example** to load the test case below and
   calculate it in one click. Empty fields show an example of what to type.
2. **Press Calculate cost.** The page scrolls down to the results.
3. **Read the answer first.** The results open with one sentence giving the total cost, then a short
   "Where the money goes" breakdown with a plain-language line for each part.
4. **Check the detail** in the year by year table. The Working section underneath shows every step
   of the hypothetical Swiss tax, the gross-up and the UK tax bands.
5. **Switch currency** between pounds and Swiss francs above the results, without recalculating.
6. **Follow a source** by clicking the small number next to any line. It opens the Sources tab with
   that entry highlighted.
7. **Print or save as PDF** with the button above the results. The printout contains only the
   results of the open tab and their sources, with the web address of each source written out.

A few things work in the background:

- Dates, salary and exchange rate are shared by the Cost estimate and Immigration tabs. Changing
  them on one tab changes them on the other.
- If you change an input after calculating, a notice says the results are out of date until you
  press the button again.
- Missing or invalid inputs are listed at the top of the form, and each one is highlighted.

## Run the tests

From the `backend` folder:

```bash
python manage.py test
```

The tests cover the UK tax bands and the personal allowance taper, the ESTV federal tax table, the
Zurich tariff, convergence of the gross-up, the social security rule, the relocation exemption, the
full test case, the immigration costs, and the API's error messages for missing or malformed input.

## The test case

| Input | Value |
|---|---|
| Route | Zurich, Switzerland to London, UK, 6 April 2026 to 5 April 2028 |
| Employee | Swiss national, single, no children, 3 years with the employer |
| Base salary | CHF 150,000 a year |
| Bonus | CHF 20,000 a year |
| Housing in London | £3,000 a month, paid to the landlord (taxable benefit in kind) |
| Relocation allowance | CHF 5,000 cash, year 1 (taxable cash) |
| Moving costs | £6,000, year 1 (qualifying relocation) |
| Temporary housing | £4,000, year 1 (qualifying relocation) |
| Exchange rate | £1 = CHF 1.10 |

The tool gives a total employer cost of about **£290,364 in year 1 and £270,463 in year 2,
£560,828 in total, or 1.81 times home pay**. Immigration costs are shown separately: **£7,756** in
total, with about 11 weeks of lead time.

## How it works

### The cost table

1. **Home pay:** salary and bonus as if the employee had stayed in Switzerland.
2. **Assignment benefits:** each tagged as taxable cash, a taxable benefit in kind, a qualifying
   relocation cost (exempt up to £8,000 in total) or not taxable.
3. **Host tax and charges paid by the employer:** UK income tax on the assignment pay, the tax on
   that tax, and the social security that applies.
4. **Deductions:** hypothetical Swiss income tax and social security. These are taken from the
   employee's pay, so they reduce the employer's cost. They are shown in brackets.

### The gross-up

`I` is the net home pay after hypothetical deductions, plus the taxable benefits. The employer pays
the UK tax `T`, which is itself taxable, so `T = UKTax(I + T)`. The tool starts with `T = 0`, works out
the tax on `I + T`, feeds that back in and repeats until the tax changes by less than 1p
(about 20 iterations here). One multiplication would be wrong, because the rate changes between bands
and the personal allowance is withdrawn between £100,000 and £125,140.

### Social security

Under Article 14 of the Convention on Social Security between the UK and Switzerland, a worker sent
to the UK by a Swiss employer for no more than 24 months stays in Swiss social security, with a
certificate of coverage. This assignment is exactly 24 months, so Swiss AHV/IV/EO and ALV continue and
no UK National Insurance is due. If you enter a longer assignment, the tool switches to UK Class 1 and
Class 1A National Insurance.

### Hypothetical Swiss tax

Federal, cantonal and communal income tax for a single person in the city of Zurich, without church
tax, using the 2026 tariffs: the ESTV federal table, the Zurich basic tariff (§ 35 StG, as indexed from
1 January 2026), the cantonal multiplier of 95% and the city multiplier of 119%. Deductions are
employee social security, the flat 3% professional expenses allowance and the insurance premium
allowance. You can check the figure with the
[ESTV tax calculator](https://swisstaxcalculator.estv.admin.ch/).

## Project structure

The code is split into a `backend` folder for everything Django and Python, and a `frontend` folder
for the page, its styles and its JavaScript.

```
backend/
  manage.py
  requirements.txt
  costestimator/          Django project settings and URLs
  estimator/
    rules/                rates, thresholds and fees as plain data
      sources.py          every official source the tool links to
      uk.py               UK income tax and NI, 2026/27
      switzerland.py      Swiss federal and Zurich tax, AHV/IV/EO and ALV, 2026
      immigration.py      visa, sponsor and ETA fees and timings
    engine/               pure Python calculations, no Django imports
      uk_tax.py           income tax bands, allowance taper, NI
      swiss_tax.py        hypothetical Swiss tax and social security
      grossup.py          iterative solver for T = UKTax(I + T)
      benefits.py         UK tax treatment of each benefit
      social_security.py  which country's system applies
      estimate.py         builds the four-section cost table
      immigration.py      visa eligibility, requirements, costs and timeline
    forms.py              input validation with readable error messages
    serializers.py        engine results to JSON
    views.py              the page and the two JSON API endpoints
    tests/                engine, API and immigration tests
frontend/
  templates/estimator/
    index.html            the single page with its three tabs
  static/estimator/
    app.js                collects the inputs, calls the API and draws the results
    app.css               layout, colours and the print layout
```

The rules are kept apart from the calculations, so a rate change is a one-line edit next to its
source. The engine has no Django dependency, which makes it easy to test. Django handles
validation, routing and the page. The front end is plain JavaScript and CSS with no framework or
build step. Django finds it through the `FRONTEND_DIR` setting in `backend/costestimator/settings.py`.

### Front end

- **Layout:** a dark page with the tabs in a sidebar that stays in view while scrolling. On narrow
  screens the sidebar becomes a row of tabs along the top.
- **Colours:** all colours are defined once at the top of `frontend/static/estimator/app.css`, so the scheme can be changed in
  one place. Printing switches to dark text on white paper.
- **Code style:** each part of the results is drawn by its own small function in `app.js`, such as
  `costSummary`, `costTable` or `eligibilityPanel`, with short comments explaining each step.

### API

Both endpoints take and return JSON.

- `POST /api/estimate/`: the cost table, a plain-language description of each section, the social
  security rule, the assumptions and the working.
- `POST /api/immigration/`: eligibility checks, requirements by category, costs and timeline.

Invalid input returns HTTP 400 with a message for each field, for example:

```json
{"error": "Some inputs need correcting.", "errors": {"base_salary_chf": ["Base salary is required."]}}
```

## Assumptions and limits

- The employee is UK tax resident in both years and leaves Swiss tax residence. UK 2026/27 rates
  (England) are used for every year, and each assignment year is treated as a full UK tax year.
- Only Zurich, Switzerland to the UK, and a single employee with no children, are supported. The
  page states this rather than offering choices, and the API rejects other values with a clear message.
- Not modelled: pension (BVG), Swiss family allowance and accident insurance, the UK Apprenticeship
  Levy, split-year treatment and personal tax reliefs.
- Fees and rates were checked on the official pages in October 2026.

## AI tools used

- **Claude Code (Anthropic):** used to help plan the project, find and cross-check the official UK
  and Swiss sources. Every rate, threshold and fee in the tool was checked against the official page it links to.
