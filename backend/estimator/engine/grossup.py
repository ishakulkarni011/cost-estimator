# Solves T = tax(I + T) by repeating the calculation until it settles.
# Tax paid by the employer is itself taxable income, so it has to be grossed up.
# One multiplication is not enough because the marginal rate changes between
# bands and the personal allowance tapers away above £100,000.

from dataclasses import dataclass, field

from .money import ZERO, dec

TOLERANCE = dec("0.01")
MAX_ITERATIONS = 200


class GrossUpError(Exception):
    pass


@dataclass
class GrossUpStep:
    iteration: int
    gross_income: object
    tax: object


@dataclass
class GrossUpResult:
    net_income: object
    tax: object
    steps: list = field(default_factory=list)

    @property
    def gross_income(self):
        return self.net_income + self.tax


def gross_up(net_income, tax_function, tolerance=TOLERANCE, max_iterations=MAX_ITERATIONS):
    net_income = dec(net_income)
    tax = ZERO
    steps = []
    # Feed the last tax figure back into the income and recalculate
    for iteration in range(1, max_iterations + 1):
        new_tax = tax_function(net_income + tax)
        steps.append(GrossUpStep(iteration, net_income + tax, new_tax))
        # Stop once the tax moves by less than a penny
        if abs(new_tax - tax) < tolerance:
            return GrossUpResult(net_income=net_income, tax=new_tax, steps=steps)
        tax = new_tax
    raise GrossUpError(f"Gross-up did not converge after {max_iterations} iterations")
