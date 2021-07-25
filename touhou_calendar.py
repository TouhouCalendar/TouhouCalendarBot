import datetime
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union, Dict, Tuple
import urllib.parse

TAG_TWITTER = 1 << 0
TAG_PIXIV = 1 << 1

@dataclass(frozen=True)
class Tag:
    name: str
    platforms: int = TAG_TWITTER | TAG_PIXIV

    def is_twitter(self) -> bool:
        return bool(self.platforms & TAG_TWITTER)

    def twitter_link(self) -> str:
        return "https://twitter.com/hashtag/"+urllib.parse.quote(self.name)

    def is_pixiv(self) -> bool:
        return bool(self.platforms & TAG_PIXIV)

    def pixiv_link(self) -> str:
        return "https://pixiv.net/tags/"+urllib.parse.quote(self.name)

@dataclass(frozen=True)
class Citation:
    name: str
    url: str

@dataclass(frozen=True)
class TouhouDay:
    month: int
    day: int
    name: str # A short name for the day
    message: str # A message to display on that day. Formatted markdown, but stripped out for Twitter.
    tags: List[Tag] 
    characters: List[str] # List of characters associated with the day, kinda ill-specified as of yet need to come up with a list of characters and filter these
    explanation: str # Plaintext description of the day's derivation. Needs copyediting to be made consistent
    explanation_short: str # Short version of above, for use with inline explanations. Defaults to full explanation if not provided.
    citations: List[Citation]

ALL_DAYS: List[TouhouDay] = []
DAYS: Dict[Tuple[int, int], List[TouhouDay]] = {}

yamldir = Path(__file__).parent.absolute()
for i in range(1,13):
    with open(str(Path(yamldir, f"days/{i}.yaml")), "r") as f:
        for day in yaml.safe_load_all(f):
            citations = []
            if day["citations"]:
                for citation in day["citations"]:
                    citations.append(Citation(citation["name"], citation["url"]))
            tags = []
            for tag in day["tags"]:
                platforms = 0
                if "twitter" in tag["platforms"]:
                    platforms |= TAG_TWITTER
                if "pixiv" in tag["platforms"]:
                    platforms |= TAG_PIXIV

                tags.append(Tag(tag["name"], platforms))

            d = (day["month"], day["day"])
            days = DAYS.get(d)
            if days is None:
                days = []
                DAYS[d] = days

            explanation = day["explanation"].strip()
            explanation_short = day.get("explanation_short", explanation)
            explanation_short = explanation_short.strip(" .,")

            touhouday = TouhouDay(
                month=day["month"],
                day=day["day"],
                name=day["name"],
                message=day["message"],
                tags=tags,
                characters=day["characters"],
                explanation=explanation,
                explanation_short=explanation_short,
                citations=citations
            )
            ALL_DAYS.append(touhouday)
            days.append(touhouday)

def days_for(day: datetime.date) -> Optional[List[TouhouDay]]:
    return DAYS.get((day.month, day.day))

def upcoming_days(startdate: datetime.date, enddate: datetime.date, min_days: int = 5) -> Tuple[datetime.date, List[TouhouDay]]:
    date = startdate
    count = 0
    while (date < enddate) or (count < min_days):
        days = days_for(date)
        if days is not None:
            count += len(days)
            yield (date, days)

        date += datetime.timedelta(days=1)

def format_twitter(day: TouhouDay) -> str:
    return f"{day.message.replace('**', '')} {' '.join('#' + tag.name for tag in day.tags if tag.is_twitter())}\n\n({day.explanation_short})"

def format_discord_embed(days: List[TouhouDay]) -> dict:
    day_messages: List[str] = []
    for day in days:
        tags: List[str] = []
        for tag in day.tags:
            taglinks: List[str] = []
            if tag.is_pixiv():
                taglinks.append(f"[pixiv]({tag.pixiv_link()})")
            if tag.is_twitter():
                taglinks.append(f"[twitter]({tag.twitter_link()})")
            tags.append(f"#{tag.name} ({'|'.join(taglinks)})")

        day_messages.append(f"{day.message} {' '.join(tags)}  \n*{day.explanation_short}*")

    return {
        "color": 13632027, # Reimu Red
        "description": "\n".join(day_messages),
    }

def format_upcoming_twitter(startdate: datetime.date, enddate: datetime.date) -> List[str]:
    lines: List[str] = []
    for date, touhoudays in upcoming_days(startdate, enddate):
        lines.append(
            f"{date.month}/{date.day}: {', '.join(day.name for day in touhoudays)}"
        )
    msg = "Upcoming:\n" + "\n".join(lines)
    chunks: List[str] = []
    while len(msg) > 280:
        delim = msg.rfind('\n', 0, 280)
        chunks.append(str(msg[0:delim]))
        msg = msg[delim+1:]
    chunks.append(str(msg))

    return chunks
    

def format_upcoming_discord_embed(startdate: datetime.date, enddate: datetime.date) -> dict:
    lines: List[str] = []
    for date, touhoudays in upcoming_days(startdate, enddate):
        lines.append(
            f"[{date.month}/{date.day}: {', '.join(day.name for day in touhoudays)}](https://touhoucalendar.github.io/#{date.month}-{date.day})"
        )

    return {
        "title": "Upcoming Days",
        "color": 16312092, # Marisa Yellow
        "description": "\n".join(lines),
    }

