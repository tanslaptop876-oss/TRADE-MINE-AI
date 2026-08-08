from dashboard.observability import (
    filter_options,
    filter_validation_runs,
    issue_frequency,
)


RUNS = [
    {
        "run_number": 1,
        "valid": True,
        "issues": [],
        "symbol": "NSE:INFY",
        "service_version": "1.7.0",
    },
    {
        "run_number": 2,
        "valid": False,
        "issues": ["risk", "cash"],
        "symbol": "NSE:TCS",
        "service_version": "1.7.0",
    },
    {
        "run_number": 3,
        "valid": False,
        "issues": ["risk"],
        "symbol": "NSE:INFY",
        "service_version": "1.8.0",
    },
]


def test_dashboard_filters_runs_by_outcome_symbol_and_version():
    assert filter_validation_runs(
        RUNS,
        outcome="invalid",
        symbol="NSE:INFY",
        service_version="1.8.0",
    ) == [RUNS[2]]


def test_dashboard_issue_frequency_is_sorted_and_counted():
    assert issue_frequency(RUNS) == [
        {"issue": "risk", "count": 2},
        {"issue": "cash", "count": 1},
    ]


def test_dashboard_filter_options_are_unique_and_sorted():
    assert filter_options(RUNS, "symbol") == [
        "all",
        "NSE:INFY",
        "NSE:TCS",
    ]
