# Changelog for engage_scraper

## v0.0.28

- Add twitter capacity with TwitterUtil class in tweet.py in scraper_utils. Must pass init values from [Twitter Developer Apps](https://developer.twitter.com/en/apps)

## v0.0.27

- Moved `POSTGRES_HOSTNAME` to `POSTGRES_HOST` for environment variable since almost all other places use host since it probably directs to a host rather than a named host.
