from touhou_calendar import days_for, format_twitter, format_discord_embed, format_upcoming_twitter, format_upcoming_discord_embed
import json
import os
import sys
import logging
import datetime
import argparse

logging.basicConfig()

parser = argparse.ArgumentParser()
parser.add_argument("--discord-only", action="store_true")
parser.add_argument("--twitter-only", action="store_true")
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

if date_utc.weekday() == 6:
    # It's Sunday, my dudes. Post a preview
    preview_start = today_jst + datetime.timedelta(days=1)
    preview_end   = preview_start + datetime.timedelta(days=14)
    twitter_preview = format_upcoming_twitter(preview_start, preview_end)
    embeds.append(format_upcoming_discord_embed(preview_start, preview_end))

if touhoudays is not None:
    embeds.append(format_discord_embed(touhoudays))

if not args.discord_only:
    if args.dry:
        #Todo: Better dry run
        if twitter_preview is not None:
            # Todo: Better split algo here?
            print(repr(twitter_preview))

        if touhoudays is not None:
            for day in touhoudays:
                #Todo: Post in reverse order of importance, so biggest day shows up first to viewers?
                print(format_twitter(day))
    else:
        try:
            APP_CONSUMER_KEY = os.environ['APP_CONSUMER_KEY']
            APP_CONSUMER_SECRET = os.environ['APP_CONSUMER_SECRET']
            ACC_TOKEN = os.environ['ACC_TOKEN']
            ACC_SECRET = os.environ['ACC_SECRET']

            import twitter
            api = twitter.Api(consumer_key=APP_CONSUMER_KEY,
                              consumer_secret=APP_CONSUMER_SECRET,
                              access_token_key=ACC_TOKEN,
                              access_token_secret=ACC_SECRET)

            if twitter_preview is not None:
                # Todo: Proper tweet split here, only relevant for heavy days
                api.PostUpdate(twitter_preview)

            if touhoudays is not None:
                for day in touhoudays:
                    #Todo: Post in reverse order of importance, so biggest day shows up first to viewers?
                    api.PostUpdate(format_twitter(day))
        except:
            logging.exception('Failed to send tweet')

if not args.twitter_only and len(embeds) > 0:
    if args.dry:
        #Todo: Better dry run
        print(embeds)
    else:
        try:
            WEBHOOK_URL = os.environ['WEBHOOK_URL']
            import requests

            resp = requests.post(WEBHOOK_URL, data={'payload_json':json.dumps({'embeds': embeds})})
            print(resp)
        except:
            logging.exception('Failed to send Discord message')
