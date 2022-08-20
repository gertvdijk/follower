from __future__ import annotations

import datetime
import json

from .utils import twitter_isodateformat_str_to_datetime


def check_tweeps(*, schermnaam: str, startdatum_str: str) -> str:
    nul_follow = 0
    has_follow = 0
    nul_tweeted = 0
    has_tweeted = 0
    twitteraars = 0
    aantal = 0
    # Assume input was in system-local timezone.
    startDate = datetime.datetime.strptime(startdatum_str, "%d-%m-%Y").astimezone()
    with open(f"{schermnaam}_followers.json", "r") as f:
        page = json.load(f)
        for creep in page:
            # Wanneer is deze lid geworden van twitter
            aanmaak = twitter_isodateformat_str_to_datetime(creep["created_at"])
            volgers = creep["followers_count"]
            tweets = creep["statuses_count"]
            # De check. Pak alleen de tweeps lid geworden na de ingegeven datum
            print(aanmaak)
            print(startDate)
            if aanmaak > startDate:
                twitteraars += 1
                print(f"{aanmaak}\t{volgers}\t{tweets}")
                if not volgers:
                    nul_follow += 1
                else:
                    has_follow += 1
                if not tweets:
                    nul_tweeted += 1
                else:
                    has_tweeted += 1
            aantal += 1

    # Procentueel
    procent_nul_volgers = int((nul_follow / twitteraars) * 100)
    procent_nul_tweets = int((nul_tweeted / twitteraars) * 100)
    # Maak de samenvatting:
    res = ""
    res += f"Aantal gecheckte volgers: {aantal}\n"
    res += f"Aantal volgers van {schermnaam} met een twitteraccount aangemaakt na "
    res += f"{startdatum_str}: {twitteraars}\n"
    res += f"\nVan die accounts hebben:\n"
    res += f"{nul_follow} volgers zelf geen volgers. Dat is afgerond "
    res += f"{procent_nul_volgers} procent\n"
    res += f"{has_follow} volgers 1 of meer volgers.\n"
    res += f"{nul_tweeted} volgers zelf nog niets getweet. Dat is afgerond "
    res += f"{procent_nul_tweets} procent\n"
    res += f"{has_tweeted} volgers 1 of meer tweets gepost.\n"

    return res
