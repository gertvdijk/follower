from __future__ import annotations

import os
import sys

from .analyse import get_follower_data
from .check import check_tweeps


def analyse_user():
    print("Geef de twitter username (zonder @) in")
    print("en de datum vanaf wanneer je informatie wilt")
    print("over volgers. Let op de aangegeven datum notatie.")
    print("Geef ook aan of je bestaande data wilt gebruiken,")
    print('je kunt ook de data opnieuw gebruiken door "n" in te geven.\n\n')

    wie = input("Twitter username: ")
    datum = input("Vanaf welke datum (dd-mm-jjj): ")
    reuse_data = input("Data opnieuw ophalen (j|n): ")

    if reuse_data == "j" or reuse_data == "J":
        try:
            if sys.platform in ("linux", "linux2", "darwin"):
                os.system("rm *.json")
            elif sys.platform == "win32":
                os.system("del *.json")
        except:
            print("No files to delete")
    elif reuse_data == "n" or reuse_data == "N":
        print("We gebruiken de bestaande data indien aanwezig.")
    else:
        print("Graag j of n ingeven. Voer het script opnieuw uit.")
        sys.exit()

    followers = get_follower_data(wie)
    test = check_tweeps(wie, datum)

    if sys.platform in ("linux", "linux2", "darwin"):
        os.system("clear")
    elif sys.platform == "win32":
        os.system("cls")

    print(followers)
    print("\n\n")
    print(test)


analyse_user()
