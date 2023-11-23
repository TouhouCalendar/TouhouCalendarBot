from touhou_calendar import days_for, format_twitter, format_discord_embed, format_upcoming_twitter, format_upcoming_discord_embed
import json
import os
import sys
import logging
import datetime
import argparse

from urllib.parse import urlparse

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument("--discord-only", action="store_true")
parser.add_argument("--twitter-only", action="store_true")
parser.add_argument("--today-only", action="store_true")
parser.add_argument("--dry", action="store_true")
parser.add_argument("--force", action="store_true")
parser.add_argument("--date")

args = parser.parse_args()

if args.date:
    if (not args.force) and (not args.dry):
        print("Date specified for non-dry run!")
        sys.exit(1)

    today_jst = datetime.date(*map(int, args.date.split("-")))
    date_utc = today_jst
else:
    JST = datetime.timezone(datetime.timedelta(hours=9), name="JST")
    today_jst = datetime.datetime.now(JST).date()

    date_utc = datetime.datetime.utcnow().date()

touhoudays = days_for(today_jst)
print(today_jst, touhoudays)

twitter_preview = None
embeds = []

if date_utc.weekday() == 6 and not args.today_only:
    # It's Sunday, my dudes. Post a preview
    preview_start = today_jst + datetime.timedelta(days=1)
    preview_end   = preview_start + datetime.timedelta(days=14)
    twitter_preview = format_upcoming_twitter(preview_start, preview_end)
    embeds.append(format_upcoming_discord_embed(preview_start, preview_end))

if touhoudays is not None:
    embeds.append(format_discord_embed(touhoudays))

if not args.twitter_only and len(embeds) > 0:
    if args.dry:
        #Todo: Better dry run
        print(json.dumps(embeds))
    else:
        WEBHOOK_URL = os.environ['WEBHOOK_URL']
        import requests
        import time

        MAX_WEBHOOK_POST_RETRIES = 5

        for webhook_url in WEBHOOK_URL.split(" "):
            for attempt in range(MAX_WEBHOOK_POST_RETRIES):
                try:
                    resp = requests.post(webhook_url+"?wait=true", json={'embeds': embeds})
                    if resp.ok:
                        print(webhook_url+"/messages/"+resp.json()["id"])

                    try:
                        rl_remaining = int(resp.headers["X-RateLimit-Remaining"])
                        if rl_remaining == 0:
                            rl_after = float(resp.headers["X-RateLimit-Reset-After"])
                            time.sleep(rl_after)
                    except:
                        logging.exception('Error handling ratelimiting from {}'.format(webhook_url))

                    if resp.ok:
                        break
                except:
                    logging.exception('Failed to send Discord message {}'.format(webhook_url))
            else:
                logging.error('Failed to send Discord message {}'.format(webhook_url))
