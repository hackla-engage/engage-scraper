# Engage Scraper

## Installation

`pip i engage-scraper`

## About

The Engage Scraper is a standalone library that can be included in any service. The purpose of the scraper is to catalog a municipality's council meeting agendas in a usable format for such things as the [engage-client](https://github.com/hackla-engage/engage-client) and [engage-backend](https://github.com/hackla-engage/engage-backend).

To extend this library for your municipality, override the methods of the base class from the `scraper_core/` directory and put it in `scraper_logics/`, prefacing it with your municipality name. For an example see the Santa Monica, CA example in the `scraper_logics/` directory. The Santa Monica example makes use of `htmlutils.py` because it requires HTML scraping for its sources. Feel free to make PRs with new utilities (for example, PDF scraping, RSS scraping, JSON parsing, etc.). The Santa Monica example also uses SQLAlchemy for its models and that is what is preferred for use in the `dbutils.py`, however you can use anything. ORMs are preferred rather than vanilla psycopg2 or the like.

To use the postgres `dbutils.py` make sure to set these two environment variables:

* `POSTGRES_URI` # a URI string of the form `username:password@hostname`
* `POSTGRES_DB`  # The database used for cataloging your municipality's agendas.

## An example of using the Santa Monica scraper library

```{python}
from engage_scraper.scraper_logics import santamonica_scraper_logic

scraper = santamonica_scraper_logic.SantaMonicaScraper(committee="Santa Monica City Council")
scraper.get_available_agendas()
scraper.scrape()
```

### For SantaMonicaScraper instantiation

parameters are:

* `tz_string="America/Los_Angeles"` # defaulted string
* `years=["2019"]` # defaulted array of strings of years
* `committee="Santa Monica City Council"` # defaulted string of council name

### The exposed API methods for scraper are

* `.get_available_agendas()` # To get available agendas, no arguments
* `.scrape()` # To process agendas and store contents

### Feel free to expose more

* Write wrappers for internal functions if you want to expose them
* Write extra functions to handle more complex municipality-specific tasks
