# Engage Scraper

The Engage Scraper is a standalone library that can be included in any service. The purpose of the scraper is to catalog a municipality's council meeting agendas in a usable format for such things as the [engage-client](https://github.com/hackla-engage/engage-client) and [engage-backend](https://github.com/hackla-engage/engage-backend).

To extend this library for your municipality, override the methods of the base class from the `scraper_core/` directory and put it in `scraper_logics/`, prefacing it with your municipality name. For an example see the Santa Monica, CA example in the `scraper_logics/` directory. The Santa Monica example makes use of `htmlutils.py` because it requires HTML scraping for its sources. Feel free to make PRs with new utilities (for example, PDF scraping, RSS scraping, JSON parsing, etc.)

To use the postgres `dbutils.py` make sure to set these two environment variables:

* `POSTGRES_URI` # a URI string of the form `username:password@hostname`
* `POSTGRES_DB`  # The database used for cataloging your municipality's agendas.
