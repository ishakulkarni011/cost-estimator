// Front end for the two tabs. All calculation happens in Django; this file
// only collects the inputs, posts them as JSON and draws the response.

// The worked example from the brief, filled in by the "Fill in the worked example" buttons
const EXAMPLE_ASSIGNMENT = {
  start_date: "2026-04-06",
  end_date: "2028-04-05",
  base_salary_chf: "150000",
  bonus_chf: "20000",
  chf_per_gbp: "1.10",
};

const EXAMPLE_IMMIGRATION = {
  start_date: "2026-04-06",
  end_date: "2028-04-05",
  base_salary_chf: "150000",
  chf_per_gbp: "1.10",
  months_with_employer: "36",
  sponsor_size: "medium_large",
};

const EXAMPLE_BENEFITS = [
  { name: "Housing in London", amount: "3000", currency: "GBP", frequency: "monthly", years: "all", treatment: "benefit_in_kind" },
  { name: "Relocation allowance", amount: "5000", currency: "CHF", frequency: "one_off", years: "first", treatment: "taxable_cash" },
  { name: "Moving costs (flights, shipping)", amount: "6000", currency: "GBP", frequency: "one_off", years: "first", treatment: "qualifying_relocation" },
  { name: "Temporary housing (4 weeks)", amount: "4000", currency: "GBP", frequency: "one_off", years: "first", treatment: "qualifying_relocation" },
];

const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;


// ---------- Small helpers ----------

// Creates an element with attributes and children, skipping empty children
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }

  for (const child of children.flat()) {
    if (child === null || child === undefined || child === "") continue;
    node.append(child instanceof Node ? child : document.createTextNode(child));
  }
  return node;
}

// Whole pounds or francs. Negative amounts are shown in brackets, as in accounts.
function formatMoney(value, currency) {
  const rounded = Math.round(value);
  const amount = Math.abs(rounded).toLocaleString("en-GB");
  const text = currency === "chf" ? `CHF ${amount}` : `£${amount}`;
  return rounded < 0 ? `(${text})` : text;
}

const gbp = (value) => formatMoney(value, "gbp");
const chf = (value) => formatMoney(value, "chf");

// Reads every named field in a form, leaving out the benefits table
function formValues(form) {
  const values = {};
  for (const field of form.querySelectorAll("input[name], select[name]")) {
    if (!field.closest("#benefit-rows")) values[field.name] = field.value.trim();
  }
  return values;
}

async function postJson(url, payload) {
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify(payload),
    });
  } catch {
    return { ok: false, body: { error: "Could not reach the server. Check that it is running and try again." } };
  }

  try {
    return { ok: response.ok, body: await response.json() };
  } catch {
    return { ok: false, body: { error: `The server sent an unexpected response (status ${response.status}).` } };
  }
}


// ---------- Source references ----------

// Collects the sources cited in one set of results. Each source gets a
// number the first time it is cited, and the full list goes in the Sources tab.
function createSourceList(prefix) {
  const numbers = new Map();
  const entries = [];

  function cite(sources) {
    if (!sources || !sources.length) return null;

    const links = sources.map((source) => {
      if (!numbers.has(source.url)) {
        entries.push(source);
        numbers.set(source.url, entries.length);
      }
      const number = numbers.get(source.url);
      return el("a", { href: `#${prefix}-${number}`, title: source.title }, String(number));
    });

    // Separate several numbers with commas, like footnotes
    const parts = links.flatMap((link, i) => (i === 0 ? [link] : [", ", link]));
    return el("sup", { class: "cite" }, parts);
  }

  // Replaces the list in the Sources tab with the sources cited this time
  function render(container) {
    container.replaceChildren(
      el("ol", { class: "source-list" },
        entries.map((source, i) =>
          el("li", { id: `${prefix}-${i + 1}` },
            el("a", { href: source.url, target: "_blank", rel: "noopener" }, source.title)))));
  }

  return { cite, render };
}

// Clicking a reference number opens the Sources tab and highlights that entry
document.addEventListener("click", (event) => {
  const link = event.target.closest(".cite a");
  if (!link) return;
  event.preventDefault();

  const entry = document.querySelector(link.getAttribute("href"));
  document.querySelectorAll(".source-list .highlight").forEach((item) => item.classList.remove("highlight"));
  entry.classList.add("highlight");

  showTab("sources");
  entry.scrollIntoView({ block: "center" });
});


// ---------- Errors ----------

function clearErrors(form, box) {
  form.querySelectorAll(".invalid").forEach((field) => field.classList.remove("invalid"));
  box.hidden = true;
}

// Lists the messages at the top of the form and highlights each bad field
function showErrors(form, box, body) {
  const messages = [];

  for (const [field, list] of Object.entries(body.errors || {})) {
    messages.push(...list);

    // Benefit errors arrive as "benefits.<row>.<field>"
    const match = field.match(/^benefits\.(\d+)\.(\w+)$/);
    const input = match
      ? form.querySelectorAll("#benefit-rows tr")[match[1]]?.querySelector(`[name=${match[2]}]`)
      : form.querySelector(`[name=${field}]`);
    input?.classList.add("invalid");
  }

  box.replaceChildren(
    el("strong", {}, body.error || "Something went wrong."),
    messages.length ? el("ul", {}, messages.map((message) => el("li", {}, message))) : null,
  );
  box.hidden = false;
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}


// ---------- Forms ----------

// Posts a form to its API, then shows either the errors or the result
function connectForm({ form, url, getPayload, errorBox, output, render }) {
  const button = form.querySelector("button[type=submit]");

  // Warns that the results on screen no longer match the form
  const staleNote = el("p", { class: "stale-note", hidden: "" },
    `You have changed the inputs. Press ${button.textContent} to update these results.`);
  output.prepend(staleNote);

  form.addEventListener("input", () => {
    if (!output.hidden) staleNote.hidden = false;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;

    const { ok, body } = await postJson(url, getPayload());
    button.disabled = false;
    clearErrors(form, errorBox);

    if (!ok) {
      showErrors(form, errorBox, body);
      output.hidden = true;
      return;
    }
    render(body);
    staleNote.hidden = true;
    output.hidden = false;

    // Only scroll when the person pressed the button, not on the first page load
    if (event.submitter) output.scrollIntoView({ behavior: "smooth" });
  });
}

// Dates, salary and exchange rate appear on both tabs. Typing in one copy
// updates the other, and the input event marks the other tab's results as stale.
const SHARED_FIELDS = ["start_date", "end_date", "base_salary_chf", "chf_per_gbp"];

function shareFields(firstForm, secondForm) {
  for (const [from, to] of [[firstForm, secondForm], [secondForm, firstForm]]) {
    from.addEventListener("input", (event) => {
      const name = event.target.name;
      if (!SHARED_FIELDS.includes(name)) return;

      const twin = to.elements[name];
      if (twin.value === event.target.value) return;
      twin.value = event.target.value;
      twin.dispatchEvent(new Event("input", { bubbles: true }));
    });
  }
}


// ---------- Tabs ----------

// Remembers how far down each tab was scrolled, so going back lands in the same place
const scrollPositions = {};
let currentTab = "cost";

function showTab(name) {
  scrollPositions[currentTab] = window.scrollY;
  currentTab = name;

  // The print layout reads this to decide which results to print
  document.body.dataset.tab = name;

  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.tab === name;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active);
  });
  document.querySelectorAll(".tab-panel").forEach((panel) => {
    panel.hidden = panel.id !== `tab-${name}`;
  });

  history.replaceState(null, "", `#${name}`);
  window.scrollTo(0, scrollPositions[name] || 0);
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => showTab(tab.dataset.tab));
});

// Keep the same tab open after a page refresh
const tabFromAddress = location.hash.slice(1);
if (["immigration", "sources"].includes(tabFromAddress)) showTab(tabFromAddress);


// ---------- Benefits table ----------

const benefitRows = document.getElementById("benefit-rows");
const rowTemplate = document.getElementById("benefit-row-template");

function addBenefitRow(benefit = {}) {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);

  for (const [key, value] of Object.entries(benefit)) {
    const field = row.querySelector(`[name=${key}]`);
    if (field) field.value = value;
  }

  row.querySelector(".remove").addEventListener("click", () => {
    row.remove();
    benefitsChanged();
  });
  benefitRows.append(row);
  return row;
}

// Adding or removing a row is a change to the form, like typing in it.
// The table is hidden while it has no rows.
function benefitsChanged() {
  const hasRows = benefitRows.children.length > 0;
  document.getElementById("benefits-table").hidden = !hasRows;
  document.getElementById("no-benefits").hidden = hasRows;
  benefitRows.closest("form").dispatchEvent(new Event("input"));
}

function benefitValues() {
  return [...benefitRows.querySelectorAll("tr")].map((row) => {
    const values = {};
    row.querySelectorAll("[name]").forEach((field) => (values[field.name] = field.value.trim()));
    return values;
  });
}

// A new empty row gets the cursor straight away
document.getElementById("add-benefit").addEventListener("click", () => {
  addBenefitRow().querySelector("[name=name]").focus();
  benefitsChanged();
});


// ---------- Cost estimate tab ----------

const costForm = document.getElementById("cost-form");
const costResult = document.getElementById("cost-result");
const currencySelect = document.getElementById("display-currency");
let lastEstimate = null;

connectForm({
  form: costForm,
  url: "/api/estimate/",
  getPayload: () => ({ ...formValues(costForm), benefits: benefitValues() }),
  errorBox: document.getElementById("cost-errors"),
  output: document.getElementById("cost-output"),
  render: (data) => {
    lastEstimate = data;
    renderEstimate();
  },
});

// Switching currency redraws the last result without asking the server again
currencySelect.addEventListener("change", () => {
  if (lastEstimate) renderEstimate();
});

function renderEstimate() {
  const data = lastEstimate;
  const currency = currencySelect.value;
  const sources = createSourceList("cost-source");

  costResult.replaceChildren(
    costSummary(data, currency),
    costTable(data, currency, sources),
    socialSecurityPanel(data, sources),
    assumptionsPanel(data, sources),
    workingPanel(data),
  );
  sources.render(document.getElementById("cost-sources"));
}

// The answer in one sentence, then how the total is made up
function costSummary(data, currency) {
  const total = data.total[`${currency}_total`];
  const years = data.years.length === 1 ? "1 year" : `${data.years.length} years`;
  const multiple = data.multiple_of_home_pay_total.toFixed(2);

  // One line per section, ending with the total
  const breakdown = data.sections.map((section) =>
    el("tr", {},
      el("td", {}, section.name, el("div", { class: "note" }, section.description)),
      el("td", { class: "num" }, formatMoney(section.subtotal[`${currency}_total`], currency))));

  return el("div", { class: "panel" },
    el("h2", {}, "The answer"),
    // Sentence on the left, breakdown on the right (stacked on small screens)
    el("div", { class: "answer-layout" },
      el("div", {},
        el("p", { class: "answer" },
          `Sending this employee to London for ${years} will cost the employer about `,
          el("strong", {}, formatMoney(total, currency)),
          `. That is ${multiple} times what they would earn at home.`),
        el("p", { class: "note" },
          `Converted at £1 = CHF ${data.chf_per_gbp.toFixed(2)}. The year by year table below shows every line.`)),
      el("div", {},
        el("h3", {}, "Where the money goes"),
        el("table", { class: "breakdown" },
          el("tbody", {}, breakdown),
          el("tfoot", {},
            el("tr", {},
              el("td", {}, "Total cost to the employer"),
              el("td", { class: "num" }, formatMoney(total, currency))))))));
}

// One cell per year followed by the whole-assignment total
function amountCells(values, currency) {
  return [
    ...values[currency].map((value) => el("td", { class: "num" }, formatMoney(value, currency))),
    el("td", { class: "num total-col" }, formatMoney(values[`${currency}_total`], currency)),
  ];
}

function costTable(data, currency, sources) {
  const columnCount = data.years.length + 2;

  const head = el("thead", {},
    el("tr", {},
      el("th", {}, "What the employer pays"),
      data.years.map((year) => el("th", { class: "num" }, year.label, el("br"), el("small", {}, year.period))),
      el("th", { class: "num total-col" }, "Whole assignment")));

  // Each section gets a heading row, its line items and a subtotal
  const body = el("tbody");
  for (const section of data.sections) {
    body.append(el("tr", {},
      el("th", { colspan: columnCount }, section.name, el("div", { class: "note" }, section.description))));

    for (const row of section.rows) {
      body.append(el("tr", {},
        el("td", {},
          row.label, sources.cite(row.sources),
          row.tag ? el("div", { class: "note" }, `UK treatment: ${row.tag}`) : null,
          row.note ? el("div", { class: "note" }, row.note) : null),
        amountCells(row, currency)));
    }

    body.append(el("tr", { class: "subtotal-row" },
      el("td", {}, `Total ${section.name.toLowerCase()}`),
      amountCells(section.subtotal, currency)));
  }

  const foot = el("tfoot", {},
    el("tr", { class: "grand-total" },
      el("td", {}, "Total cost to the employer"),
      amountCells(data.total, currency)),
    el("tr", {},
      el("td", {}, "Cost as a multiple of home pay"),
      data.multiple_of_home_pay.map((multiple) => el("td", { class: "num" }, multiple.toFixed(2))),
      el("td", { class: "num total-col" }, data.multiple_of_home_pay_total.toFixed(2))));

  return el("div", { class: "panel" },
    el("h2", {}, "Year by year"),
    el("div", { class: "table-scroll" }, el("table", { class: "cost-table" }, head, body, foot)),
    el("p", { class: "note" },
      "Figures in brackets are deducted from the employee's pay and reduce the employer's cost. ",
      el("span", { class: "screen-only" }, "Click a small number next to a line to see its source in the Sources tab.")));
}

function socialSecurityPanel(data, sources) {
  const regime = data.social_security;
  return el("div", { class: "panel" },
    el("h2", {}, "Social security during the assignment"),
    el("p", {}, el("strong", {}, regime.title), sources.cite(regime.sources)),
    el("p", {}, regime.explanation));
}

function assumptionsPanel(data, sources) {
  return el("div", { class: "panel" },
    el("h2", {}, "Assumptions"),
    el("ul", { class: "assumptions" },
      data.assumptions.map((item) => el("li", {}, item.text, sources.cite(item.sources)))));
}

function workingPanel(data) {
  return el("div", { class: "panel" },
    el("h2", {}, "Working"),
    el("p", { class: "note screen-only" }, "Open a year to see how each figure was reached."),
    data.working.map(workingForYear));
}

// A simple two-column table of label and amount. Rows marked strong are totals.
function workingTable(rows) {
  return el("table", { class: "working-table" },
    el("tbody", {},
      rows.map(([label, value, strong]) =>
        el("tr", { class: strong ? "strong" : "" },
          el("td", {}, label),
          el("td", { class: "num" }, value)))));
}

function workingForYear(year) {
  return el("details", { class: "working" },
    el("summary", {}, `Year ${year.year}: hypothetical tax, tax on tax and UK tax bands`),
    el("div", { class: "working-grid" },
      hypotheticalTaxWorking(year.hypothetical_chf),
      grossUpWorking(year),
      ukBandsWorking(year)));
}

function hypotheticalTaxWorking(h) {
  return el("div", {},
    el("h3", {}, "Hypothetical Swiss tax in CHF"),
    workingTable([
      ["Salary and bonus", chf(h.gross_salary)],
      ["Less employee AHV/IV/EO and ALV", chf(h.social_security)],
      ["Less professional expenses (3%, at most 4,000)", chf(h.federal_professional_expenses)],
      ["Less insurance premiums (federal)", chf(h.federal_insurance_deduction)],
      ["Federal taxable income, rounded down to 100", chf(h.federal_taxable_income), true],
      ["Federal tax (ESTV 2026 tariff)", chf(h.federal_tax)],
      ["Zurich taxable income (insurance 2,900)", chf(h.zurich_taxable_income), true],
      ["Simple state tax (Zurich tariff)", chf(h.zurich_simple_tax)],
      ["Cantonal tax, 95% of simple tax", chf(h.zurich_cantonal_tax)],
      ["City of Zurich tax, 119% of simple tax", chf(h.zurich_communal_tax)],
      ["Personal tax", chf(h.zurich_personal_tax)],
      ["Hypothetical Swiss income tax", chf(h.total_tax), true],
    ]));
}

function grossUpWorking(year) {
  const steps = year.grossup_steps;

  // Long runs show the first five and last two steps only
  const hidden = steps.length > 8 ? steps.length - 7 : 0;
  const shown = hidden ? [...steps.slice(0, 5), null, ...steps.slice(-2)] : steps;

  const stepRows = shown.map((step) => step
    ? el("tr", {},
        el("td", {}, step.iteration),
        el("td", { class: "num" }, gbp(step.gross_income)),
        el("td", { class: "num" }, gbp(step.tax)))
    : el("tr", {}, el("td", { colspan: 3, class: "muted" }, `${hidden} more steps not shown`)));

  return el("div", {},
    el("h3", {}, "Tax on tax"),
    workingTable([
      ["Net home pay after hypothetical deductions", gbp(year.net_home_pay_gbp)],
      ["Plus taxable benefits", gbp(year.taxable_benefits_gbp)],
      ["UK taxable pay before tax (I)", gbp(year.income_before_tax_gbp), true],
    ]),
    el("table", { class: "working-table" },
      el("thead", {},
        el("tr", {},
          el("th", {}, "Step"),
          el("th", { class: "num" }, "Pay plus tax"),
          el("th", { class: "num" }, "UK tax on that"))),
      el("tbody", {}, stepRows)),
    el("p", { class: "note" },
      `The tax settled after ${steps.length} steps at ${gbp(year.uk_tax_gbp)}.`));
}

function ukBandsWorking(year) {
  const bands = year.uk_bands;
  return el("div", {},
    el("h3", {}, "UK income tax for 2026/27"),
    workingTable([
      ["Gross taxable income", gbp(year.gross_taxable_income_gbp)],
      ["Personal allowance (after the £100,000 taper)", gbp(bands.personal_allowance)],
      ...bands.bands.map((band) => [
        `${band.name}, ${Math.round(band.rate * 100)}% on ${gbp(band.income)}`,
        gbp(band.tax),
      ]),
    ]));
}


// ---------- Immigration tab ----------

const immigrationForm = document.getElementById("immigration-form");
const immigrationResult = document.getElementById("immigration-result");

connectForm({
  form: immigrationForm,
  url: "/api/immigration/",
  getPayload: () => formValues(immigrationForm),
  errorBox: document.getElementById("immigration-errors"),
  output: document.getElementById("immigration-output"),
  render: renderImmigration,
});

function renderImmigration(data) {
  const sources = createSourceList("visa-source");

  immigrationResult.replaceChildren(
    immigrationSummary(data),
    eligibilityPanel(data, sources),
    ...data.categories.map((category) => requirementsPanel(category, sources)),
    timelinePanel(data),
  );
  sources.render(document.getElementById("immigration-sources"));
}

// The answer in one sentence, then the two figures people plan around
function immigrationSummary(data) {
  const answer = data.eligible
    ? `The employee needs a ${data.route} to work in the UK, and meets the requirements for it.`
    : `The employee needs a ${data.route} to work in the UK, but does not yet meet every requirement. See Eligibility below.`;

  return el("div", { class: "panel" },
    el("h2", {}, "The answer"),
    el("p", { class: "answer" }, answer),
    el("div", { class: "summary" },
      el("div", {},
        el("span", { class: "label" }, "Total fees"),
        el("span", { class: "figure" }, gbp(data.costs.total)),
        el("small", {}, `Employer ${gbp(data.costs.employer)}, employee ${gbp(data.costs.employee)}`)),
      el("div", {},
        el("span", { class: "label" }, "How long it takes"),
        el("span", { class: "figure" }, `About ${data.timeline.total_weeks} weeks`),
        el("small", {}, `Start by ${data.timeline.start_by} to be ready on the start date`))));
}

// Each visa test with a plain Met or Not met next to it
function eligibilityPanel(data, sources) {
  const verdict = data.eligible
    ? "The employee meets every requirement checked here."
    : "The employee does not meet every requirement. See the items marked Not met.";

  return el("div", { class: "panel" },
    el("h2", {}, "Eligibility"),
    el("p", {}, verdict),
    el("ul", { class: "checks" },
      data.checks.map((check) =>
        el("li", {},
          el("span", { class: `status ${check.passed ? "met" : "not-met"}` }, check.passed ? "Met" : "Not met"),
          el("div", {},
            el("strong", {}, check.label), sources.cite(check.sources),
            el("div", { class: "note" }, check.detail))))));
}

function requirementsPanel(category, sources) {
  const rows = category.requirements.map((item) =>
    el("tr", {},
      el("td", {},
        el("strong", {}, item.title), sources.cite(item.sources),
        el("div", { class: "note" }, item.detail)),
      el("td", {}, item.time),
      el("td", { class: "num" }, item.cost_gbp ? gbp(item.cost_gbp) : ""),
      el("td", {}, item.paid_by)));

  return el("div", { class: "panel" },
    el("h2", {}, category.name),
    el("div", { class: "table-scroll" },
      el("table", { class: "req-table" },
        el("thead", {},
          el("tr", {},
            el("th", {}, "Requirement"),
            el("th", {}, "How long"),
            el("th", { class: "num" }, "Cost"),
            el("th", {}, "Paid by"))),
        el("tbody", {}, rows))));
}

function timelinePanel(data) {
  return el("div", { class: "panel" },
    el("h2", {}, "Timeline"),
    el("ol", { class: "timeline" },
      data.timeline.steps.map((step) =>
        el("li", {}, step.step, step.weeks ? el("span", { class: "muted" }, `, up to ${step.weeks} weeks`) : null))),
    el("p", { class: "note" },
      "Fees are as listed on GOV.UK when this tool was built. " +
      "The employer usually reimburses the employee's visa fee and health surcharge."));
}


shareFields(costForm, immigrationForm);


// ---------- Printing ----------

document.querySelectorAll(".print-button").forEach((button) => {
  button.addEventListener("click", () => window.print());
});

// Open every Working section for the printout, then close them again afterwards.
// The list is added to rather than replaced, in case the browser fires beforeprint twice.
let closedForPrint = [];

window.addEventListener("beforeprint", () => {
  const closed = [...document.querySelectorAll("details.working:not([open])")];
  closed.forEach((section) => (section.open = true));
  closedForPrint.push(...closed);
});

window.addEventListener("afterprint", () => {
  closedForPrint.forEach((section) => (section.open = false));
  closedForPrint = [];
});


// ---------- Worked example ----------

// Sets each field and fires an input event, so shared fields and stale notes update too
function fillForm(form, values) {
  for (const [name, value] of Object.entries(values)) {
    const field = form.elements[name];
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

const examples = {
  cost: () => {
    fillForm(costForm, EXAMPLE_ASSIGNMENT);
    benefitRows.replaceChildren();
    EXAMPLE_BENEFITS.forEach((benefit) => addBenefitRow(benefit));
    benefitsChanged();
    return costForm;
  },
  immigration: () => {
    fillForm(immigrationForm, EXAMPLE_IMMIGRATION);
    return immigrationForm;
  },
};

// Fill in the example, then calculate straight away so the results appear
document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    const form = examples[button.dataset.example]();
    form.requestSubmit(form.querySelector("button[type=submit]"));
  });
});
