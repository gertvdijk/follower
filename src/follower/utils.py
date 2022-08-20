from __future__ import annotations

import datetime


def twitter_isodateformat_str_to_datetime(datestr: str) -> datetime.datetime:
    # Twitter returns datetime strings which are naive, representing UTC.
    return datetime.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=datetime.timezone.utc
    )
