import pytest
from datetime import date, time, timedelta

from solution import TimeWindow, BusyInterval, Slot, suggest_slots


# Covers C1, AC4
def test_slots_sorted_chronologically():
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [BusyInterval(start=time(10, 0), end=time(10, 30))]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=4,
        buffer=timedelta(0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(10, 30)),
        Slot(start_time=time(11, 0)),
    ]


# Covers C2, AC3
def test_slots_do_not_overlap_busy_intervals():
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))
    busy_intervals = [BusyInterval(start=time(9, 30), end=time(10, 0))]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(10, 0)),
        Slot(start_time=time(10, 30)),
    ]


# Covers C3, AC5
def test_return_at_most_n_slots():
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(15, 0))

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=[],
        duration=timedelta(minutes=30),
        n=3,
        buffer=timedelta(0)
    )

    assert len(result) == 3
    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(10, 0)),
    ]


# Covers C4, AC4
def test_deterministic_output():
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [
        BusyInterval(start=time(10, 0), end=time(10, 30)),
        BusyInterval(start=time(11, 0), end=time(11, 30)),
    ]

    result1 = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(0)
    )

    result2 = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(0)
    )

    assert result1 == result2


# Covers C5, AC8
def test_tie_breaking_order():
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=[],
        duration=timedelta(minutes=30),
        n=4,
        buffer=timedelta(0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(10, 0)),
        Slot(start_time=time(10, 30)),
    ]


# Covers C6, AC2
def test_overlapping_intervals_normalized():
    # Edge case
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(13, 0))
    busy_intervals = [
        BusyInterval(start=time(11, 0), end=time(12, 0)),
        BusyInterval(start=time(10, 0), end=time(11, 30)),
    ]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=4,
        buffer=timedelta(0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(12, 0)),
        Slot(start_time=time(12, 30)),
    ]


# Covers C6, AC2
def test_adjacent_intervals_normalized():
    # Edge case
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [
        BusyInterval(start=time(10, 0), end=time(10, 30)),
        BusyInterval(start=time(10, 30), end=time(11, 0)),
    ]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(11, 0)),
        Slot(start_time=time(11, 30)),
    ]


# Covers C7, AC6
def test_invalid_inputs_raise_error():
    day = date(2026, 3, 7)

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=TimeWindow(start=time(17, 0), end=time(9, 0)),
            busy_intervals=[],
            duration=timedelta(minutes=30),
            n=2,
            buffer=timedelta(0)
        )

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=TimeWindow(start=time(9, 0), end=time(17, 0)),
            busy_intervals=[],
            duration=timedelta(minutes=0),
            n=2,
            buffer=timedelta(0)
        )

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=TimeWindow(start=time(9, 0), end=time(17, 0)),
            busy_intervals=[],
            duration=timedelta(minutes=30),
            n=2,
            buffer=timedelta(minutes=-5)
        )


# Covers C8, AC7
def test_no_available_slots_returns_empty():
    # Edge case
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [
        BusyInterval(start=time(9, 0), end=time(10, 0)),
        BusyInterval(start=time(10, 0), end=time(11, 0)),
        BusyInterval(start=time(11, 0), end=time(12, 0)),
    ]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(0)
    )

    assert result == []
