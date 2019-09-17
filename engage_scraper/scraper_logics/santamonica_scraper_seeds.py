from .santamonica_scraper_models import Committee


def seed_tables(Session):
    session = Session()
    if len(session.query(Committee).all()) == 0:
        session.add(Committee(name="Santa Monica City Council",
                              email="engage@engage.town",
                              cutoff_offset_days=0,
                              cutoff_hour=12,
                              cutoff_minute=0
                              ))
        session.commit()