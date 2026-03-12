## Student Name: Dieng Fatoumata
## Student ID: 219904564

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple

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
    Invariant: start < end.
    """
    start: time
    end: time


@dataclass(frozen=True)
class Slot:
    """
    A recommended appointment slot.
    start_time is a time-of-day within the working window.
    """
    start_time: time


class InfeasibleSchedule(Exception):
    """Reserved for future use if the specification requires exception-based handling."""
    pass


# ---------------- Helper Functions ----------------

def _combine(day: date, t: time) -> datetime:
    return datetime.combine(day, t)


def _validate_time_window(window: TimeWindow, name: str) -> None:
    if window.start >= window.end:
        raise ValueError(f"{name} must satisfy start < end.")


def _validate_busy_intervals(busy_intervals: List[BusyInterval]) -> None:
    for interval in busy_intervals:
        if interval.start >= interval.end:
            raise ValueError("Each busy interval must satisfy start < end.")


def _clip_interval(
    start_dt: datetime,
    end_dt: datetime,
    clip_start: datetime,
    clip_end: datetime
) -> Optional[Tuple[datetime, datetime]]:
    clipped_start = max(start_dt, clip_start)
    clipped_end = min(end_dt, clip_end)

    if clipped_start >= clipped_end:
        return None

    return (clipped_start, clipped_end)


def _merge_intervals(
    intervals: List[Tuple[datetime, datetime]]
) -> List[Tuple[datetime, datetime]]:
    """
    Merge overlapping or adjacent intervals.
    Deterministic ordering is preserved by sorting by (start, end).
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


def _window_intersection(
    day: date,
    working_hours: TimeWindow,
    candidate_window: Optional[TimeWindow]
) -> Tuple[datetime, datetime]:
    work_start = _combine(day, working_hours.start)
    work_end = _combine(day, working_hours.end)

    if candidate_window is None:
        return work_start, work_end

    _validate_time_window(candidate_window, "candidate_window")

    candidate_start = _combine(day, candidate_window.start)
    candidate_end = _combine(day, candidate_window.end)

    effective_start = max(work_start, candidate_start)
    effective_end = min(work_end, candidate_end)

    return effective_start, effective_end


def _normalize_busy_intervals(
    day: date,
    busy_intervals: List[BusyInterval],
    search_start: datetime,
    search_end: datetime
) -> List[Tuple[datetime, datetime]]:
    clipped: List[Tuple[datetime, datetime]] = []

    for interval in busy_intervals:
        start_dt = _combine(day, interval.start)
        end_dt = _combine(day, interval.end)

        clipped_interval = _clip_interval(start_dt, end_dt, search_start, search_end)
        if clipped_interval is not None:
            clipped.append(clipped_interval)

    return _merge_intervals(clipped)


def _generate_slots_in_free_block(
    free_start: datetime,
    free_end: datetime,
    duration: timedelta,
    n_remaining: int
) -> List[Slot]:
    """
    Generate fixed-duration slots within a free block.
    Slots are produced in deterministic chronological order.
    """
    results: List[Slot] = []
    current = free_start

    while current + duration <= free_end and len(results) < n_remaining:
        results.append(Slot(start_time=current.time()))
        current += duration

    return results


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
    Suggest up to the next n valid appointment slots for the given day.

    Persona-aware behavior supported here:
    - deterministic chronological ordering
    - automatic conflict handling
    - concise output (at most n results)
    - explicit invalid-input rejection
    - explicit handling of edge cases such as overlap, adjacency, and no availability

    Returns:
        A list of Slot objects sorted by start_time ascending.
        Returns [] when no valid slot exists.
    """
    _validate_time_window(working_hours, "working_hours")
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

    if search_start + duration > search_end:
        return []

    normalized_busy = _normalize_busy_intervals(day, busy_intervals, search_start, search_end)

    suggestions: List[Slot] = []
    current_start = search_start

    for busy_start, busy_end in normalized_busy:
        # Free block ends before busy interval, respecting pre-busy buffer
        free_end = busy_start - buffer

        if current_start < free_end and len(suggestions) < n:
            new_slots = _generate_slots_in_free_block(
                current_start,
                free_end,
                duration,
                n - len(suggestions)
            )
            suggestions.extend(new_slots)

        # Move current_start to first valid post-busy time respecting buffer
        current_start = max(current_start, busy_end + buffer)

        if len(suggestions) >= n:
            return suggestions

    # Final free block after the last busy interval
    if current_start < search_end and len(suggestions) < n:
        suggestions.extend(
            _generate_slots_in_free_block(
                current_start,
                search_end,
                duration,
                n - len(suggestions)
            )
        )

    return suggestions
