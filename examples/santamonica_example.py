from __future__ import absolute_import
from engage_scraper.scraper_logics.santamonica_scraper_logic import SantaMonicaScraper
from engage_scraper.scraper_logics.santamonica_scraper_models import AgendaRecommendation
from os import getenv
from random import randrange
smscraper = SantaMonicaScraper(years=getenv("ENGAGE_COMMITTEE_YEARS", "2020").split(","), test=True)
smscraper.set_committee("Santa Monica City Council")
smscraper.get_available_agendas()
smscraper.scrape()
recommendations = smscraper._DBsession().query(AgendaRecommendation).all()
for recommendation in recommendations:
    print(recommendation.recommendation)