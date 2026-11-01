from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
PENNY = Decimal("0.01")


# Turns an int, float or string into a Decimal without float rounding noise.
def dec(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_money(value):
    return dec(value).quantize(PENNY, rounding=ROUND_HALF_UP)


# Rounds down to a multiple of step, e.g. floor_to(153_559.80, 100) gives 153_500.
def floor_to(value, step):
    step = dec(step)
    return (dec(value) / step).to_integral_value(rounding=ROUND_DOWN) * step


def chf_to_gbp(amount_chf, chf_per_gbp):
    return dec(amount_chf) / dec(chf_per_gbp)


def gbp_to_chf(amount_gbp, chf_per_gbp):
    return dec(amount_gbp) * dec(chf_per_gbp)
