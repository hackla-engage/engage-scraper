import os
import twitter

consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
access_token_key = os.getenv("ACCESS_TOKEN_KEY")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

class TwitterUtil:
    def __init__(self):
        self._api = twitter.Api(consumer_key=consumer_key,
                               consumer_secret=consumer_secret,
                               access_token_key=access_token_key,
                               access_token_secret=access_token_secret)

    def tweet(self, status, media = None):
        """
        Post a string status message and optionally a media object to add to the tweet
        """
        if (media is not None):
            # for adding url or image (media may be a fp)
            self._api.PostUpdate(status, media=media)
        else:
            self._api.PostUpdate(status)