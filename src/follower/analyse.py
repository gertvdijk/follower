from __future__ import annotations

import collections
import dataclasses
import datetime
import io
import json
import os
import sys
import typing

import tweepy
import tweepy.API
import tweepy.OAuthHandler

from .utils import twitter_isodateformat_str_to_datetime

# Get the twitter credentials from a (hidden) file
secrets = open(".login")
login = secrets.readlines()

# assign the values accordingly
# strip the linebreak from the values to prevent bad login errors
consumer_key = login[0].rstrip("\n")
consumer_secret = login[1].rstrip("\n")
access_token = login[2].rstrip("\n")
access_token_secret = login[3].rstrip("\n")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
auth_api = tweepy.API(auth, wait_on_rate_limit=True)

# Helper functions to load and save intermediate steps
def save_json(variable: typing.Any, filename: typing.AnyStr) -> None:
    with io.open(filename, "w", encoding="utf-8") as f:
        f.write(str(json.dumps(variable, indent=4, ensure_ascii=False)))


def load_json(filename: str) -> typing.Any:
    print(f"Loading {str(filename)}")

    ret = None
    if os.path.exists(filename):
        try:
            with io.open(filename, "r", encoding="utf-8") as f:
                ret = json.load(f)
        except:
            pass
    return ret


def try_load_or_process(filename: str, processor_fn, function_arg) -> typing.Any:
    if not filename.endswith(".json"):
        raise RuntimeError("Only .json files are supported to process.")

    if os.path.exists(filename):
        return load_json(filename)
    else:
        ret = processor_fn(function_arg)
        print(f"Saving {str(filename)}")
        save_json(ret, filename)
        return ret


# Get a list of follower ids for the target account
def get_follower_ids(target: str) -> list[str]:
    ids: list[str] = []
    for page in tweepy.Cursor(auth_api.get_follower_ids, screen_name=target).pages():
        assert isinstance(page, list)
        assert all((isinstance(item, str) for item in page))
        ids.extend(page)

    return ids


# Twitter API allows us to batch query 100 accounts at a time.
# So we'll create batches of 100 follower ids and gather Twitter User objects for each
# batch.
def get_user_objects(
    follower_ids: list[str], *, batch_size: int = 100
) -> list[typing.Any]:
    num_batches = len(follower_ids) / batch_size
    batches = (
        follower_ids[i : i + batch_size]
        for i in range(0, len(follower_ids), batch_size)
    )
    all_data: list[typing.Any] = []
    for batch_count, batch in enumerate(batches):
        sys.stdout.write("\r")
        sys.stdout.flush()
        sys.stdout.write("Fetching batch: " + str(batch_count) + "/" + str(num_batches))
        sys.stdout.flush()
        sys.stdout.write("\n")
        sys.stdout.flush()
        users_list: typing.Any = auth_api.lookup_users(user_id=batch)
        users_json: typing.Any = map(lambda t: t._json, users_list)
        all_data += users_json
    return all_data


@dataclasses.dataclass(kw_only=True)
class TwitterAccountDetails:
    id: int
    created_at: datetime.datetime
    screen_name: str
    name: str
    friends_count: int
    followers_count: int
    favourites_count: int
    statuses_count: int

    @classmethod
    def from_api_obj(
        cls, api_obj: typing.Any, *, created_at: datetime.datetime | None = None
    ) -> TwitterAccountDetails:
        return TwitterAccountDetails(
            id=api_obj["id_str"],
            created_at=created_at
            or twitter_isodateformat_str_to_datetime(api_obj["created_at"]),
            screen_name=api_obj["screen_name"],
            name=api_obj["name"],
            friends_count=api_obj["friends_count"],
            followers_count=api_obj["followers_count"],
            favourites_count=api_obj["favourites_count"],
            statuses_count=api_obj["statuses_count"],
        )


@dataclasses.dataclass(kw_only=True)
class AccountAgeRange:
    label: str
    lower: datetime.datetime
    upper: datetime.datetime
    accounts: set[TwitterAccountDetails] = dataclasses.field(default_factory=set)

    def in_range(self, account_created_at: datetime.datetime) -> bool:
        return account_created_at >= self.lower and account_created_at < self.upper


def make_ranges(
    user_data: typing.Iterable[typing.Any], num_ranges: int = 10
) -> list[AccountAgeRange]:
    """
    Creates one week length ranges and match accounts which are created within the
    boundaries of each.
    """
    range_step = datetime.timedelta(days=7)
    now = datetime.datetime.now(datetime.timezone.utc)

    account_age_ranges = [
        AccountAgeRange(
            label=f"{i} - {i + 1} weeks",
            lower=now - (range_step * (i + 1)),
            upper=now - (range_step * i),
        )
        for i in range(num_ranges)
    ]

    for user_api_obj in user_data:
        if "created_at" not in user_api_obj:
            continue
        created_at = twitter_isodateformat_str_to_datetime(user_api_obj["created_at"])
        for account_age_range in account_age_ranges:
            if account_age_range.in_range(created_at):
                account_age_range.accounts.add(
                    TwitterAccountDetails.from_api_obj(
                        user_api_obj, created_at=created_at
                    )
                )
                break
    return account_age_ranges


def get_follower_data(screen_name: str) -> str:
    print(f"Processing target: {screen_name}")

    # Get a list of Twitter ids for followers of target account and save it
    filename = f"{screen_name}_follower_ids.json"
    follower_ids = try_load_or_process(filename, get_follower_ids, screen_name)

    # Fetch Twitter User objects from each Twitter id found and save the data
    filename = f"{screen_name}_followers.json"
    user_objects = try_load_or_process(filename, get_user_objects, follower_ids)
    total_objects = len(user_objects)

    # Record a few details about each account that falls between specified age ranges
    ranges = make_ranges(user_objects)
    filename = f"{screen_name}_ranges.json"
    save_json(ranges, filename)

    # Print a few summaries
    res = "\n"
    res += "Follower age ranges\n"
    res += "===================\n"
    total = 0
    for account_age_range in ranges:
        label, entries = account_age_range.label, account_age_range.accounts
        res += f"{len(entries)} accounts were created within {label}\n"
        total += len(entries)
    res += f"Total: {total}/{total_objects}\n"

    return res
