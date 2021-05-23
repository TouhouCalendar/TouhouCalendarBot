from touhou_calendar import *
import re
import json
import datetime
from twitter_text import TwitterText
import requests
from typing import Set

LINK_REGEX = re.compile("https?://")

daycount = 0
tagcount = 0
for month,day in DAYS:
    days = DAYS[month, day]

    for day in days:
        dayname = f"{day.name} ({day.month}/{day.day})"
        if not any(tag.is_twitter() for tag in day.tags):
            print(f"Day {dayname} has no Twitter tags!")
        if not any(tag.is_pixiv() for tag in day.tags):
            print(f"Day {dayname} has no Pixiv tags!")

        tagnames: Set[str] = set()
        for tag in day.tags:
            if tag.name.startswith("#"):
                print(f"Day {dayname} has improper tag {tag}!")

            if tag.name in tagnames:
                print(f"Day {dayname} has duplicate tag {tag}!")
            tagnames.add(tag.name)

            if not tag.is_twitter() and not tag.is_pixiv():
                print(f"Day {dayname} has tag with no platform!")

            if tag.is_twitter():
                twittertext = TwitterText("#"+tag.name)
                if not twittertext.validation.valid_hashtag():
                    print(f"Day {dayname} has invalid twitter tag {tag}!")

            tagcount += 1

        if len(day.citations) == 0:
            print(f"Day {dayname} has no citations!")

        if LINK_REGEX.search(day.explanation):
            print(f"Day {dayname} has links in explanation!")

        tweettext = format_twitter(day)
        invalid = TwitterText(tweettext).validation.tweet_invalid()
        if invalid:
            print(f"Day {dayname} invalid tweet text: {invalid}! \"{tweettext}\"")

        #for citation in day.citations:
        #    r = requests.head(citation.url, allow_redirects=True)
        #    if r.status_code != 200:
        #        print("Day {} citation {} status code {}!".format(day.name, citation.url, r.status_code))

        daycount += 1
print(f"Checked {daycount} days with {tagcount} tags.")

twitter_previews = []
for month, day in DAYS:
    preview_start = datetime.date(2020, month, day)
    preview_end   = preview_start + datetime.timedelta(days=14)
    twitter_previews.append(format_upcoming_twitter(preview_start, preview_end))

with open("previews", "w") as f:
    json.dump(twitter_previews, f)

