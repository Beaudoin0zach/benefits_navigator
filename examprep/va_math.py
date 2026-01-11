"""
VA Combined Rating Calculator - Accurate Implementation

The VA uses a "whole person" theory for combining disability ratings.
Each rating is applied to the remaining "healthy" percentage, not added directly.

References:
- 38 CFR § 4.25 - Combined ratings table
- 38 CFR § 4.26 - Bilateral factor
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DisabilityRating:
    """Individual disability rating"""
    percentage: int
    description: str = ""
    is_bilateral: bool = False
    bilateral_group: str = ""  # e.g., "upper", "lower" for grouping


@dataclass
class CalculationResult:
    """Result of VA combined rating calculation"""
    combined_raw: float
    combined_rounded: int
    bilateral_factor_applied: float
    step_by_step: List[dict]
    ratings_used: List[DisabilityRating]
    estimated_monthly: Optional[float] = None


def validate_rating(percentage: int) -> bool:
    """
    Validate that a rating is a valid VA disability percentage.
    VA ratings must be 0-100 in increments of 10.
    """
    return 0 <= percentage <= 100 and percentage % 10 == 0


def combine_two_ratings(rating1: int, rating2: int) -> float:
    """
    Combine two disability ratings using VA Math formula.

    Formula: A + B(1-A) = Combined
    Where A and B are expressed as decimals.

    Example: 50% + 30%
    - 0.50 + 0.30(1 - 0.50) = 0.50 + 0.30(0.50) = 0.50 + 0.15 = 0.65 = 65%
    """
    # Convert to decimals
    a = rating1 / 100.0
    b = rating2 / 100.0

    # Apply formula: combined = A + B(1-A)
    combined = a + b * (1 - a)

    return combined * 100


def combine_multiple_ratings(ratings: List[int]) -> Tuple[float, List[dict]]:
    """
    Combine multiple disability ratings in order from highest to lowest.

    Returns the combined percentage (not rounded) and step-by-step calculations.
    """
    if not ratings:
        return 0.0, []

    if len(ratings) == 1:
        return float(ratings[0]), [{
            'step': 1,
            'rating': ratings[0],
            'combined_before': 0,
            'combined_after': float(ratings[0]),
            'explanation': f"Single rating: {ratings[0]}%"
        }]

    # Sort ratings highest to lowest (VA requirement)
    sorted_ratings = sorted(ratings, reverse=True)

    steps = []
    combined = float(sorted_ratings[0])

    steps.append({
        'step': 1,
        'rating': sorted_ratings[0],
        'combined_before': 0,
        'combined_after': combined,
        'explanation': f"Start with highest rating: {sorted_ratings[0]}%"
    })

    for i, rating in enumerate(sorted_ratings[1:], start=2):
        before = combined
        combined = combine_two_ratings(int(round(combined)), rating)

        remaining = 100 - before
        contribution = rating * remaining / 100

        steps.append({
            'step': i,
            'rating': rating,
            'combined_before': before,
            'combined_after': combined,
            'remaining_healthy': remaining,
            'contribution': contribution,
            'explanation': (
                f"Add {rating}%: {rating}% × {remaining:.1f}% remaining = "
                f"{contribution:.1f}% → Combined: {combined:.1f}%"
            )
        })

    return combined, steps


def calculate_bilateral_factor(bilateral_ratings: List[int]) -> Tuple[float, float]:
    """
    Calculate the bilateral factor for paired extremity conditions.

    Per 38 CFR § 4.26:
    1. Combine all bilateral ratings
    2. Add 10% of that combined value as the bilateral factor

    Returns: (combined_bilateral, bilateral_factor_bonus)
    """
    if not bilateral_ratings:
        return 0.0, 0.0

    combined, _ = combine_multiple_ratings(bilateral_ratings)

    # Bilateral factor is 10% of the combined bilateral rating
    bilateral_factor = combined * 0.10

    return combined, bilateral_factor


def round_to_nearest_10(value: float) -> int:
    """
    Round combined rating to nearest 10% per VA rules.

    Per 38 CFR § 4.25:
    - 0.5 and above rounds up
    - Below 0.5 rounds down

    Examples:
    - 65% rounds to 70%
    - 64% rounds to 60%
    - 75% rounds to 80%
    """
    # Use Decimal for precise rounding
    d = Decimal(str(value))
    # Divide by 10, round to nearest integer, multiply by 10
    rounded = int(Decimal(d / 10).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 10)
    return min(100, max(0, rounded))


def calculate_combined_rating(ratings: List[DisabilityRating]) -> CalculationResult:
    """
    Calculate combined VA disability rating with full bilateral factor support.

    Process:
    1. Separate bilateral and non-bilateral ratings
    2. Combine bilateral ratings and add 10% bilateral factor
    3. Combine bilateral result with non-bilateral ratings
    4. Round to nearest 10%
    """
    if not ratings:
        return CalculationResult(
            combined_raw=0.0,
            combined_rounded=0,
            bilateral_factor_applied=0.0,
            step_by_step=[],
            ratings_used=[]
        )

    # Separate bilateral and non-bilateral ratings
    bilateral_ratings = [r for r in ratings if r.is_bilateral]
    non_bilateral_ratings = [r for r in ratings if not r.is_bilateral]

    all_steps = []
    bilateral_factor_bonus = 0.0

    # Process bilateral ratings if any
    bilateral_combined = 0.0
    if bilateral_ratings:
        bilateral_percentages = [r.percentage for r in bilateral_ratings]
        bilateral_combined, bilateral_steps = combine_multiple_ratings(bilateral_percentages)

        # Add bilateral factor (10% of combined bilateral)
        bilateral_factor_bonus = bilateral_combined * 0.10
        bilateral_with_factor = bilateral_combined + bilateral_factor_bonus

        all_steps.append({
            'phase': 'bilateral',
            'description': 'Bilateral Conditions (paired extremities)',
            'ratings': bilateral_percentages,
            'combined': bilateral_combined,
            'bilateral_factor': bilateral_factor_bonus,
            'total_with_factor': bilateral_with_factor,
            'steps': bilateral_steps
        })

        # The bilateral total (with factor) is treated as one rating
        all_percentages = [bilateral_with_factor] + [r.percentage for r in non_bilateral_ratings]
    else:
        all_percentages = [r.percentage for r in non_bilateral_ratings]

    # Combine all ratings
    if all_percentages:
        # Convert to integers for combination (bilateral total might be float)
        int_percentages = [int(round(p)) for p in all_percentages]
        final_combined, final_steps = combine_multiple_ratings(int_percentages)

        all_steps.append({
            'phase': 'final',
            'description': 'Final Combination',
            'ratings': int_percentages,
            'combined_raw': final_combined,
            'steps': final_steps
        })
    else:
        final_combined = 0.0

    # Round to nearest 10%
    rounded = round_to_nearest_10(final_combined)

    return CalculationResult(
        combined_raw=final_combined,
        combined_rounded=rounded,
        bilateral_factor_applied=bilateral_factor_bonus,
        step_by_step=all_steps,
        ratings_used=ratings
    )


# 2024 VA Compensation Rates (effective December 1, 2023)
# These are monthly rates for veterans with no dependents
VA_COMPENSATION_RATES_2024 = {
    0: 0.00,
    10: 171.23,
    20: 338.49,
    30: 524.31,
    40: 755.28,
    50: 1075.16,
    60: 1361.88,
    70: 1716.28,
    80: 1995.01,
    90: 2241.91,
    100: 3737.85,
}

# Additional amounts for dependents at 30%+ rating
DEPENDENT_RATES_2024 = {
    'spouse': {
        30: 62.00, 40: 83.00, 50: 104.00, 60: 125.00,
        70: 146.00, 80: 166.00, 90: 187.00, 100: 208.38
    },
    'child_under_18': {
        30: 31.00, 40: 41.00, 50: 52.00, 60: 62.00,
        70: 72.00, 80: 83.00, 90: 93.00, 100: 103.55
    },
    'parent_one': {
        30: 54.00, 40: 71.00, 50: 89.00, 60: 107.00,
        70: 125.00, 80: 143.00, 90: 161.00, 100: 178.63
    }
}


def estimate_monthly_compensation(
    combined_rating: int,
    spouse: bool = False,
    children_under_18: int = 0,
    dependent_parents: int = 0
) -> float:
    """
    Estimate monthly VA disability compensation.

    Note: This is an estimate. Actual rates depend on many factors
    including effective date, special monthly compensation, etc.
    """
    if combined_rating not in VA_COMPENSATION_RATES_2024:
        return 0.0

    base = VA_COMPENSATION_RATES_2024[combined_rating]
    total = base

    # Dependents only add to 30%+ ratings
    if combined_rating >= 30:
        if spouse and combined_rating in DEPENDENT_RATES_2024['spouse']:
            total += DEPENDENT_RATES_2024['spouse'][combined_rating]

        for _ in range(children_under_18):
            if combined_rating in DEPENDENT_RATES_2024['child_under_18']:
                total += DEPENDENT_RATES_2024['child_under_18'][combined_rating]

        for _ in range(min(2, dependent_parents)):  # Max 2 parents
            if combined_rating in DEPENDENT_RATES_2024['parent_one']:
                total += DEPENDENT_RATES_2024['parent_one'][combined_rating]

    return round(total, 2)


def format_currency(amount: float) -> str:
    """Format amount as USD currency"""
    return f"${amount:,.2f}"
