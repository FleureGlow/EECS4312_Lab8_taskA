## Student Name: Dieng Fatoumata
## Student ID:v 219904564

"""
Task A: Appointment Timeslot Recommender (Stub)

In this lab, you will design and implement an Appointment Slot Recommender using an LLM assistant
as your primary programming collaborator.

You are asked to implement a Python module that recommends available meeting slots within a
defined working window.

The system must:
  • Accept working hours (start and end time).
  • Accept a list of existing busy intervals.
  • Accept a required meeting duration.
  • Accept an optional buffer time between meetings.
  • Optionally restrict suggestions to a candidate time window.
  • Return chronologically ordered appointment slots that satisfy all constraints.

The system must ensure that:
  • Suggested slots fall within working hours.
  • Suggested slots do not overlap busy intervals.
  • Buffer time is respected when evaluating availability.
  • Output ordering is deterministic under identical inputs.

The module must preserve the following invariants:
  • Returned slots must be at least as long as the required duration.
  • No returned slot may violate buffer constraints.
  • The returned list must reflect the current system state.

The system must correctly handle non-trivial scenarios such as:
  • Adjacent busy intervals.
  • Very small gaps between meetings.
  • Buffers eliminating otherwise valid availability.
  • Overlapping or unsorted busy intervals.
  • A meeting duration longer than any available gap.
  • No availability within the working window.

Output:
  The output consists of the next N valid appointment suggestions in chronological order.
  Behavior must be deterministic under ties (if any).

See the lab handout for full requirements.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional


# ---------------- Data Models ----------------

@dataclass(frozen=True)
class TimeWindow:
    """
    A daily time window.
    Assumption: non-wrapping window where start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class BusyInterval:
    """
    A busy interval on the given day.
    Invariant: start < end
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.

    start_time is a time-of-day within the working window.
    Deterministic ordering: sort by start_time ascending.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Raised when no valid slots can be produced (if required by handout)."""
    pass


# ---------------- Helper Functions ----------------

def _combine(day: date, t: time) -> datetime:
    """Combine a date and time into a datetime."""
    return datetime.combine(day, t)


def _validate_time_window(window: TimeWindow, name: str) -> None:
    """Validate that a time window is non-wrapping and has positive length."""
    if window.start >= window.end:
        raise ValueError(f"{name} must satisfy start < end.")


def _validate_busy_intervals(busy_intervals: List[BusyInterval]) -> None:
    """Validate that each busy interval has positive length."""
    for interval in busy_intervals:
        if interval.start >= interval.end:
            raise ValueError("Each busy interval must satisfy start < end.")


def _clip_interval(
    start_dt: datetime,
    end_dt: datetime,
    clip_start: datetime,
    clip_end: datetime
) -> Optional[tuple[datetime, datetime]]:
    """
    Clip an interval to a window.
    Returns None if there is no overlap.
    """
    clipped_start = max(start_dt, clip_start)
    clipped_end = min(end_dt, clip_end)

    if clipped_start >= clipped_end:
        return None

    return (clipped_start, clipped_end)


def _merge_intervals(
    intervals: List[tuple[datetime, datetime]]
) -> List[tuple[datetime, datetime]]:
    """
    Merge overlapping or adjacent intervals.
    Deterministic: sort by start, then end.
    """
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda pair: (pair[0], pair[1]))
    merged = [intervals[0]]

    for current_start, current_end in intervals[1:]:
        last_start, last_end = merged[-1]

        # Merge overlapping or adjacent intervals
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))

    return merged


def _normalize_busy_intervals(
    day: date,
    busy_intervals: List[BusyInterval],
    search_start: datetime,
    search_end: datetime
) -> List[tuple[datetime, datetime]]:
    """
    Convert busy intervals to datetimes, clip them to the search window,
    then merge overlapping/adjacent intervals.
    """
    clipped_intervals: List[tuple[datetime, datetime]] = []

    for interval in busy_intervals:
        start_dt = _combine(day, interval.start)
        end_dt = _combine(day, interval.end)

        clipped = _clip_interval(start_dt, end_dt, search_start, search_end)
        if clipped is not None:
            clipped_intervals.append(clipped)

    return _merge_intervals(clipped_intervals)


def _window_intersection(
    day: date,
    working_hours: TimeWindow,
    candidate_window: Optional[TimeWindow]
) -> tuple[datetime, datetime]:
    """
    Compute the effective search window.
    If candidate_window is provided, intersect it with working_hours.
    """
    work_start = _combine(day, working_hours.start)
    work_end = _combine(day, working_hours.end)

    if candidate_window is None:
        return work_start, work_end

    candidate_start = _combine(day, candidate_window.start)
    candidate_end = _combine(day, candidate_window.end)

    effective_start = max(work_start, candidate_start)
    effective_end = min(work_end, candidate_end)

    return effective_start, effective_end


# ---------------- Core Function ----------------

def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:
    """
    Suggest up to the next n valid appointment slots (start times) for the given day.

    Args:
        day: the calendar day for which to suggest slots.
        working_hours: the allowed working window for meetings (start < end).
        busy_intervals: list of busy time intervals (may be overlapping / unsorted).
        duration: required meeting length (must be > 0).
        n: maximum number of slot suggestions to return (n >= 0).
        buffer: optional buffer time required between meetings (buffer >= 0).
        candidate_window: optional extra restriction on suggestions (must lie within this window too).

    Returns:
        A list of Slot objects, sorted by start_time ascending, deterministic under identical inputs.
        If no suitable time slots are available, return an empty list.

    Notes:
        - Suggested slots must fall within working_hours (and candidate_window if provided).
        - Suggested slots must not overlap busy_intervals, considering buffer time.
        - Internal search uses 1-minute granularity.
    """
    _validate_time_window(working_hours, "working_hours")

    if candidate_window is not None:
        _validate_time_window(candidate_window, "candidate_window")

    _validate_busy_intervals(busy_intervals)

    if duration <= timedelta(0):
        raise ValueError("duration must be greater than 0.")

    if buffer < timedelta(0):
        raise ValueError("buffer must be greater than or equal to 0.")

    if n < 0:
        raise ValueError("n must be greater than or equal to 0.")

    if n == 0:
        return []

    search_start, search_end = _window_intersection(day, working_hours, candidate_window)

    # No usable search range
    if search_start >= search_end:
        return []

    # If duration itself cannot fit, return no slots
    if search_start + duration > search_end:
        return []

    normalized_busy = _normalize_busy_intervals(day, busy_intervals, search_start, search_end)

    slots: List[Slot] = []
    current_start = search_start

    for busy_start, busy_end in normalized_busy:
        # Latest possible end before this busy interval, respecting buffer
        free_end = busy_start - buffer

        while current_start + duration <= free_end and len(slots) < n:
            slots.append(Slot(start_time=current_start.time()))
            current_start += duration

        # Earliest start after this busy interval, respecting buffer
        current_start = max(current_start, busy_end + buffer)

        if len(slots) >= n:
            return slots

    # Handle free time after the last busy interval
    while current_start + duration <= search_end and len(slots) < n:
        slots.append(Slot(start_time=current_start.time()))
        current_start += duration

    return slots
