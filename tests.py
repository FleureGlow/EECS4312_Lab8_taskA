import pytest
from datetime import date, time, timedelta

from solution import TimeWindow, BusyInterval, Slot, suggest_slots


def test_slots_within_working_hours():
    # Validates: C6, AC1
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [BusyInterval(start=time(10, 0), end=time(10, 30))]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=3,
        buffer=timedelta(minutes=0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(10, 30)),
    ]


def test_overlapping_unsorted_busy_intervals_are_normalized():
    # Validates: C4, AC2
    # Edge case: overlapping + unsorted busy intervals
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
        buffer=timedelta(minutes=0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(12, 0)),
        Slot(start_time=time(12, 30)),
    ]


def test_no_returned_slot_overlaps_busy_interval():
    # Validates: C5, AC3
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))
    busy_intervals = [BusyInterval(start=time(9, 30), end=time(10, 0))]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(minutes=0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(10, 0)),
        Slot(start_time=time(10, 30)),
    ]


def test_invalid_working_hours_raise_value_error():
    # Validates: C1, AC4
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(17, 0), end=time(9, 0))

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=working_hours,
            busy_intervals=[],
            duration=timedelta(minutes=30),
            n=2,
            buffer=timedelta(minutes=0)
        )


def test_invalid_duration_raises_value_error():
    # Validates: C2, AC5
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(17, 0))

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=working_hours,
            busy_intervals=[],
            duration=timedelta(minutes=0),
            n=2,
            buffer=timedelta(minutes=0)
        )


def test_invalid_buffer_raises_value_error():
    # Validates: C3, AC6
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(17, 0))

    with pytest.raises(ValueError):
        suggest_slots(
            day=day,
            working_hours=working_hours,
            busy_intervals=[],
            duration=timedelta(minutes=30),
            n=2,
            buffer=timedelta(minutes=-5)
        )


def test_adjacent_busy_intervals_leave_no_gap():
    # Validates: C4, C5, AC2, AC3
    # Edge case: adjacent busy intervals
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
        buffer=timedelta(minutes=0)
    )

    assert result == [
        Slot(start_time=time(9, 0)),
        Slot(start_time=time(9, 30)),
        Slot(start_time=time(11, 0)),
        Slot(start_time=time(11, 30)),
    ]


def test_buffer_eliminates_otherwise_valid_availability():
    # Validates: C3, C5, AC6, AC3
    # Edge case: buffer removes a slot that would otherwise fit
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))
    busy_intervals = [BusyInterval(start=time(9, 30), end=time(10, 0))]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=30),
        n=5,
        buffer=timedelta(minutes=15)
    )

    assert result == [
        Slot(start_time=time(10, 15)),
    ]


def test_meeting_duration_longer_than_any_gap_returns_empty():
    # Edge case: duration longer than any available gap
    day = date(2026, 3, 7)
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))
    busy_intervals = [
        BusyInterval(start=time(9, 30), end=time(10, 30)),
        BusyInterval(start=time(11, 0), end=time(11, 30)),
    ]

    result = suggest_slots(
        day=day,
        working_hours=working_hours,
        busy_intervals=busy_intervals,
        duration=timedelta(minutes=45),
        n=5,
        buffer=timedelta(minutes=0)
    )

    assert result == []
