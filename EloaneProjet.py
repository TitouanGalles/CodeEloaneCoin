import os
import random
import time
from threading import Thread
from flask import Flask
from openai import OpenAI
import tweepy

# === OpenAI client (nouvelle API >=1.0.0) ===
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# === Twitter API v2 client ===
twitter_api_key = os.getenv("TWITTER_API_KEY")
twitter_api_secret = os.getenv("TWITTER_API_SECRET")
twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
twitter_access_secret = os.getenv("TWITTER_ACCESS_SECRET")
twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

client_twitter = tweepy.Client(
    bearer_token=twitter_bearer_token,
    consumer_key=twitter_api_key,
    consumer_secret=twitter_api_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_secret,
    wait_on_rate_limit=True
)

# Get bot's own user id once
bot_user = client_twitter.get_user(username="YourTwitterUsername")  # change to your username here
bot_user_id = bot_user.data.id

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

    response = client.chat.completions.create(
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

    return response.choices[0].message.content.strip()

# === Generate reply to mention in guru style ===
def generate_reply(mention_text, username):
    prompt = f"A Twitter user @{username} mentioned the crypto guru. Respond with prophetic blockchain wisdom in under 280 characters."

    response = client.chat.completions.create(
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

    return response.choices[0].message.content.strip()

# === Main bot loop ===
def run_bot():
    global last_replied_id

    while True:
        # Tweet a new guru-style tweet
        try:
            tweet = generate_tweet()
            client_twitter.create_tweet(text=tweet)
            print("🔮 Tweeted:", tweet)
        except Exception as e:
            print("❌ Error tweeting:", e)

        # Reply to mentions since last replied id
        try:
            mentions_response = client_twitter.get_users_mentions(
                id=bot_user_id,
                since_id=last_replied_id,
                max_results=10,
                tweet_fields=["author_id", "conversation_id", "created_at", "in_reply_to_user_id"]
            )
            mentions = mentions_response.data or []
            for mention in reversed(mentions):
                # Fetch username of the mention's author
                user_response = client_twitter.get_user(id=mention.author_id)
                username = user_response.data.username

                print(f"✨ New mention from @{username}: {mention.text}")
                reply_text = generate_reply(mention.text, username)

                # Reply to the mention
                client_twitter.create_tweet(
                    text=f"@{username} {reply_text}",
                    in_reply_to_tweet_id=mention.id
                )
                print("🧘 Replied with:", reply_text)
                last_replied_id = mention.id
        except Exception as e:
            print("❌ Error replying to mentions:", e)

        time.sleep(3)  # 1 hour delay

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
