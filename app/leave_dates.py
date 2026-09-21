"""
Deterministic leave-date parsing for EmployeeMate.

No LLM and, importantly, NO silent defaults: if the dates can't be read,
extract_leave_dates() raises ValueError with a message you can show the user,
and apply_leave must NOT be called.

Supported formats (day-first for numeric dates):
    2026-09-20        20-09-2026 / 20/09/2026 / 20.09.2026
    20 September      20th Sept 2026        September 20        Sep 20th, 2026
Missing year -> current year. Past dates are allowed on purpose.
Days requested = end - start + 1 (inclusive, weekends counted).

Run the self-checks:  python leave_dates.py
"""
import re
from datetime import date

_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
           "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
_MONTH = (r"(?:january|february|march|april|may|june|july|august|september|"
          r"october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|"
          r"oct|nov|dec)")
_ORD = r"(?:st|nd|rd|th)?"

_ISO = r"\d{4}-\d{1,2}-\d{1,2}"
_NUMERIC = r"\d{1,2}[-/.]\d{1,2}[-/.]\d{4}"
_DAY_MONTH = rf"\d{{1,2}}{_ORD}\s+{_MONTH}\b\.?(?:,?\s+\d{{4}})?"
_MONTH_DAY = rf"{_MONTH}\b\.?\s+\d{{1,2}}{_ORD}\b(?:,?\s+\d{{4}})?"

_TOKEN_RE = re.compile(
    rf"\b(?:{_ISO}|{_NUMERIC}|{_DAY_MONTH}|{_MONTH_DAY})", re.IGNORECASE
)


def _parse_token(token: str, today: date) -> date:
    t = token.lower().strip().rstrip(".")

    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t)
    if m:
        return date(int(m[1]), int(m[2]), int(m[3]))

    m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", t)
    if m:
        return date(int(m[3]), int(m[2]), int(m[1]))

    m = re.fullmatch(rf"(\d{{1,2}}){_ORD}\s+({_MONTH})\.?(?:,?\s+(\d{{4}}))?", t)
    if m:
        day, month, year = int(m[1]), m[2], m[3]
    else:
        m = re.fullmatch(rf"({_MONTH})\.?\s+(\d{{1,2}}){_ORD}(?:,?\s+(\d{{4}}))?", t)
        if not m:
            raise ValueError(token)
        month, day, year = m[1], int(m[2]), m[3]

    return date(int(year) if year else today.year, _MONTHS[month[:3]], day)


def extract_leave_dates(message: str, today: date | None = None):
    """Return (start_date, end_date, days). Raises ValueError with a user-facing message."""
    today = today or date.today()
    tokens = [m.group(0) for m in _TOKEN_RE.finditer(message)]

    if not tokens:
        raise ValueError(
            "I couldn't read any dates. Please give them like "
            "'from 20 September to 22 September' or '20-09-2026 to 22-09-2026'."
        )
    if len(tokens) > 2:
        raise ValueError("Please give just a start date and an end date.")

    dates = []
    for tok in tokens:
        try:
            dates.append(_parse_token(tok, today))
        except ValueError:
            raise ValueError(f"'{tok}' is not a valid date.") from None

    start = dates[0]
    end = dates[1] if len(dates) == 2 else dates[0]  # one date = single-day leave
    if end < start:
        raise ValueError("The end date is before the start date.")
    return start, end, (end - start).days + 1


if __name__ == "__main__":
    TODAY = date(2026, 9, 20)

    good = {
        "Apply leave from 20-09-2026 to 25-09-2026": (date(2026, 9, 20), date(2026, 9, 25), 6),
        "Apply leave for EMP001 from 20 September to 22 September because I'm travelling.":
            (date(2026, 9, 20), date(2026, 9, 22), 3),
        "Apply leave for EMP001 from 20 Sept to 22 Sept.": (date(2026, 9, 20), date(2026, 9, 22), 3),
        "leave from 2026-10-01 to 2026-10-02": (date(2026, 10, 1), date(2026, 10, 2), 2),
        "from Oct 5th to Oct 7th for a family function": (date(2026, 10, 5), date(2026, 10, 7), 3),
        "apply leave on 20/09/2026": (date(2026, 9, 20), date(2026, 9, 20), 1),
    }
    for msg, expected in good.items():
        got = extract_leave_dates(msg, TODAY)
        assert got == expected, f"{msg!r}: expected {expected}, got {got}"

    bad = [
        "Apply leave from 22 September to 20 September",  # end before start
        "Apply leave tomorrow",                            # no dates -> must not guess
        "Apply leave from 31 February to 2 March",         # invalid date
    ]
    for msg in bad:
        try:
            extract_leave_dates(msg, TODAY)
        except ValueError as e:
            print(f"OK (rejected): {msg!r} -> {e}")
        else:
            raise AssertionError(f"should have been rejected: {msg!r}")

    print("All leave_dates checks passed.")