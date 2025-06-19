import os
import openai
import tweepy
import random
import time
from threading import Thread
from flask import Flask

# === API KEYS (via variables d'environnement) ===
openai.api_key = os.getenv("OPENAI_API_KEY")
api_key = os.getenv("TWITTER_API_KEY")
api_secret = os.getenv("TWITTER_API_SECRET")
access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_secret = os.getenv("TWITTER_ACCESS_SECRET")

# === Twitter Auth ===
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
api = tweepy.API(auth)

last_replied_id = None

# === Guru-style tweet generation ===
def generate_tweet():
    prompt = random.choice([
        "Speak like a crypto guru and give a mysterious prediction.",
        "Say something spiritual about Bitcoin or Ethereum.",
        "Deliver a blockchain prophecy.",
        "Make a tweet as if Satoshi Nakamoto returned.",
        "Drop alpha from the astral DeFi plane."
    ])

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a mysterious, visionary crypto guru. You speak in riddles, spiritual metaphors, and blockchain wisdom. Always tweet in English, under 280 characters."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.4,
        max_tokens=100
    )

    return response.choices[0].message["content"].strip()

# === Generate reply to mention in guru style ===
def generate_reply(mention_text, username):
    prompt = f"A Twitter user @{username} mentioned the crypto guru. Respond with prophetic blockchain wisdom in under 280 characters."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a wise crypto guru with spiritual insight into DeFi, memecoins, and the future. Speak like a prophet. Keep replies mysterious, respectful, and in English."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.3,
        max_tokens=100
    )

    return response.choices[0].message["content"].strip()

# === Main bot loop ===
def run_bot():
    global last_replied_id

    while True:
        try:
            tweet = generate_tweet()
            api.update_status(tweet)
            print("🔮 Tweeted:", tweet)
        except Exception as e:
            print("❌ Error tweeting:", e)

        try:
            mentions = api.mentions_timeline(since_id=last_replied_id, tweet_mode='extended')
            for mention in reversed(mentions):
                print(f"✨ New mention from @{mention.user.screen_name}: {mention.full_text}")
                reply = generate_reply(mention.full_text, mention.user.screen_name)
                api.update_status(
                    status=f"@{mention.user.screen_name} {reply}",
                    in_reply_to_status_id=mention.id
                )
                print("🧘 Replied with:", reply)
                last_replied_id = mention.id
        except Exception as e:
            print("❌ Error replying to mentions:", e)

        time.sleep(3600)  # 1 hour delay

# === Flask app to bind port ===
app = Flask(__name__)

@app.route("/")
def home():
    return "Crypto Guru Bot is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    # Run bot in a separate thread so Flask can run simultaneously
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()

    app.run(host="0.0.0.0", port=port)
