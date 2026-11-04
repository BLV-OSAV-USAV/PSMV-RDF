from decimal import Decimal

import numpy as np
import pytest

from src.python.utils.helper_functions import format_psm


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("12.5000", "12.5"),
        ("1.236", "1.24"),
        ("0.0100", "0.01"),
        ("0.002300", "0.0023"),
        ("0.00045", "0.00045"),
    ],
)
def test_register_examples(raw, expected):
    assert format_psm(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("0.1", "0.1"),
        ("0.10", "0.1"),
        ("0.105", "0.11"),   # just above: 2 decimals
        ("0.0995", "0.1"),   # just below: 2 significant digits
    ],
)
def test_boundary_at_0_1(raw, expected):
    assert format_psm(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2.665", "2.67"),     # half-even would give 2.66
        ("0.00125", "0.0013"), # half-even would give 0.0012
        ("-2.675", "-2.68"),   # away from zero, also for negatives
    ],
)
def test_rounds_half_away_from_zero(raw, expected):
    assert format_psm(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("100", "100"),
        ("50.00", "50"),
        ("1000", "1000"),
        ("0", "0"),
        ("0.000", "0"),
    ],
)
def test_whole_numbers_and_zero(raw, expected):
    assert format_psm(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("-12.345", "-12.35"),
        ("-0.0023", "-0.0023"),
    ],
)
def test_negative_values(raw, expected):
    assert format_psm(raw) == expected


def test_no_exponent_notation_for_tiny_values():
    assert format_psm("0.0000001234") == "0.00000012"


@pytest.mark.parametrize(
    "raw, expected",
    [
        (2.675, "2.68"),
        (np.float64(2.675), "2.68"),  # what pandas actually hands over
        (12, "12"),
        (Decimal("1.236"), "1.24"),
    ],
    ids=["float", "numpy-float64", "int", "decimal"],
)
def test_input_types(raw, expected):
    assert format_psm(raw) == expected