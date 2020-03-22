import os
import re
from datetime import datetime, timedelta
import requests
import unicodedata
from ..scraper_core.engage_scraper_core import EngageScraper
from ..scraper_utils.dbutils import create_postgres_connection, create_postgres_session, create_postgres_tables
from ..scraper_utils.htmlutils import bs4_data_from_url, parse_query_params, check_style_special
from ..scraper_utils.timeutils import string_datetime_to_timestamp, timestamp_to_month_date
from ..scraper_utils.textutils import check_last_word
from .santamonica_scraper_models import Agenda, AgendaItem, AgendaRecommendation, Committee, Base
from .santamonica_scraper_seeds import seed_tables
from ..scraper_utils.tweet import TwitterUtil
from ..scraper_utils.elasticsearch import ElasticsearchUtility
import logging
logging.basicConfig()
log = logging.getLogger(__name__)

SCRAPER_DEBUG = os.getenv('SCRAPER_DEBUG', "False") == "True"
SCRAPER_VERBOSE_DEBUG = os.getenv('SCRAPER_VERBOSE_DEBUG', "False") == "True"
CONSUMER_KEY = os.getenv('TWITTER_CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('TWITTER_CONSUMER_SECRET')
ACCESS_TOKEN_KEY = os.getenv('TWITTER_ACCESS_TOKEN_KEY')
ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
SPACE_REGEX = re.compile(r"[ \n]{2,}")
ITEM_REGEX = re.compile(r"^[0-9]{1,3}.\W+")
EMPTY_REGEX = re.compile(r"^[, ]$")
DOT_REGEX = re.compile(r"^·\W+")
ES_ENABLED = os.environ.get('ES_ENABLED', 'False') == 'True'
TWITTER_ENABLED = os.getenv('TWITTER_ENABLED', 'False') == 'True'


class SantaMonicaScraper(EngageScraper):
    def __init__(self, tz_string="America/Los_Angeles", years=["2020"], test=False):
        super().__init__(tz_string)

        # Requests/HTML session
        self._session = requests.Session()

        # For DB connection, make sure necessary environment variables are set
        self._engine = create_postgres_connection()
        self._DBsession = create_postgres_session(self._engine)

        # For tweeting
        if TWITTER_ENABLED:
            self._twitter_util = TwitterUtil(CONSUMER_KEY,
                                             CONSUMER_SECRET,
                                             ACCESS_TOKEN_KEY,
                                             ACCESS_TOKEN_SECRET)

        # Create tables
        create_postgres_tables(Base, self._engine)
        seed_tables(self._DBsession)

        # Extra SM specific parameters
        self._years = years

        # Instantiate elasticsearch utility object
        if ES_ENABLED:
            self._elasticsearch_utility = ElasticsearchUtility()
        self._test = test

    @property
    def agendas_table_location(self):
        return self._agendas_table_location

    @agendas_table_location.setter
    def agendas_table_location(self, table_location):
        self._agendas_table_location = table_location

    @property
    def base_agenda_location(self):
        return self._base_agenda_location

    @base_agenda_location.setter
    def base_agenda_location(self, base_location):
        self._base_agenda_location = base_location

    def set_committee(self, committee_name):
        committee = self._DBsession().query(Committee).filter(
            Committee.name == committee_name).first()
        if committee is not None:
            self._Committee = committee
            self._agendas_table_location = self._Committee.agendas_table_location
            self.base_agenda_location = self._Committee.base_agenda_location

    def get_available_agendas(self):
        if self._Committee is None:
            return
        """
        First gets the agenda main page to retrieve updated ASPX embeded content
        """
        soup_agenda_locations_html = bs4_data_from_url(
            self.agendas_table_location, self._session, "GET")
        form = soup_agenda_locations_html.find('form', {'name': 'aspnetForm'})
        formInputs = form.findChildren('input')
        payload = dict()
        for input in formInputs:
            if input.get('name') in [
                "EktronClientManager",
                "__VIEWSTATE",
                "__VIEWSTATEGENERATOR",
                "__EVENTVALIDATION"
            ]:
                payload[input.get('name')] = input.get('value')
        agenda_urls = []
        """
        Search for all agendas for all years
        """
        for year in self._years:
            payload["ctl00$ctl00$bodyContent$mainContent$ddlYears"] = str(year)
            soup = bs4_data_from_url(
                self.agendas_table_location, self._session, "POST", payload)
            table = soup.find('table', {'class': 'agendaTable'})
            if table is None:
                return None
            rows = table.findAll('tr')
            for row in rows:
                cells = row.findChildren('td')
                if cells[1].string == "Agenda":
                    agenda_urls.append(cells[1].findChildren(
                        'a', {'href': True})[0]['href'])
        self.agenda_locations = agenda_urls

    def scrape(self):
        """
        scrape only unprocessed agendas
        """
        if self._Committee is None:
            return
        session = self._DBsession()
        committeeid = self._Committee.id
        committees_meetings = session.query(Agenda).filter(
            Agenda.committee_id == committeeid).all()
        meetings_already_scraped = []
        for agenda in committees_meetings:
            agenda_items = session.query(AgendaItem).filter(
                AgendaItem.agenda_id == agenda.id).all()
            if len(agenda_items) > 0:
                meetings_already_scraped.append(agenda.meeting_id)
        meetings_already_scraped = sorted(meetings_already_scraped)
        agenda_meeting_ids_available = sorted(list(
            map(lambda x: x.split("=")[1], self.agenda_locations)))

        agenda_ids_to_scrape = list(filter(
            lambda x: x not in meetings_already_scraped, agenda_meeting_ids_available))
        if SCRAPER_DEBUG:
            log.error(f"AGENDA IDS TO SCRAPE: {agenda_ids_to_scrape}")

        # Since we don't want to scrape everything just scrape what we need
        updated_agenda_locations = [
            self.base_agenda_location + meeting_id for meeting_id in agenda_ids_to_scrape]
        self.agenda_locations = updated_agenda_locations
        # Get the data
        scraped_agendas = dict()
        for agenda_url in self.agenda_locations:
            if SCRAPER_DEBUG:
                log.error(agenda_url)
            data = bs4_data_from_url(agenda_url, self._session, "GET")
            params = parse_query_params(agenda_url)
            if "ID" in params:
                processed_data = self._process_agenda(data, params["ID"])
                if SCRAPER_VERBOSE_DEBUG:
                    log.error("PROCESSED DATA: {} XXX".format(processed_data))
                if processed_data is not None:
                    agenda = processed_data
                    meeting_time = processed_data["meeting_time"]
                    if SCRAPER_DEBUG:
                        log.error(meeting_time)
                        log.error(agenda["meeting_id"])
                    if len(agenda["items"]) > 0:
                        stored_agenda = self._store_agenda(agenda)
                        # now store items
                        self._store_agenda_items(agenda, stored_agenda)
                        newdate = timestamp_to_month_date(
                            meeting_time, self._tz)
                        if (newdate[0]):
                            if SCRAPER_DEBUG:
                                log.error("Sending tweet for {} meeting {} at {}".format(
                                    self._Committee.name, agenda["meeting_id"], meeting_time))
                            if TWITTER_ENABLED:
                                self._twitter_util.tweet(
                                    "Agenda Items for the next @santamonicacity City Council meeting is open for public feedback until 11:59:59AM {}. Head to http://sm.engage.town now to voice your opinion!".format(newdate[1]))
                        if self._test and agenda["meeting_id"] == '1182':
                            break

    def _process_agenda(self, agenda_data, meeting_id):
        date_time_string = agenda_data.find(
            'span', {'id': 'ContentPlaceholder1_lblMeetingDate'}).get_text()
        timestamp = string_datetime_to_timestamp(
            date_time_string, "%m/%d/%Y %I:%M %p", self._tz)
        meeting = agenda_data.find('table', {'id': 'MeetingDetail'})
        if meeting is None:
            return None
        root_item_url = "http://santamonicacityca.iqm2.com/Citizens/"
        document_structure_keys = ['SPECIAL AGENDA ITEMS', 'CONSENT CALENDAR', 'STUDY SESSION',
                                   'CONTINUED ITEMS', 'ADMINISTRATIVE PROCEEDINGS', 'ORDINANCES',
                                   'STAFF ADMINISTRATIVE ITEMS', 'PUBLIC HEARINGS']
        processed_agenda = {
            "meeting_id": meeting_id,
            "meeting_time": timestamp,
            "SPECIAL AGENDA ITEMS": [],
            "CONSENT CALENDAR": [],
            "STUDY SESSION": [],
            "CONTINUED ITEMS": [],
            "ADMINISTRATIVE PROCEEDINGS": [],
            "ORDINANCES": [],
            "STAFF ADMINISTRATIVE ITEMS": [],
            "PUBLIC HEARINGS": [],
        }
        meeting_trs = meeting.find_all('tr')
        current_section = None
        for tr in enumerate(meeting_trs):
            strong_element = tr[1].find_all('strong')
            if len(strong_element) > 1:
                strong_element_text = strong_element[-1].get_text()
                if strong_element_text in document_structure_keys:
                    current_section = strong_element_text
            else:
                if current_section and current_section == "REPORTS OF BOARDS AND COMMISSIONS":
                    break
                elif current_section:
                    ahrefs = tr[1].find_all('a', href=True)
                    for a in ahrefs:
                        if "Detail_LegiFile" in a['href'] and root_item_url not in a['href'] and meeting_id in a['href']:
                            # This is an agenda item (root_item_url in href means
                            # it's a link from a past item)
                            scraped_item_data = self._scrape_agenda_item(
                                root_item_url+a['href'])
                            params = parse_query_params(a['href'])
                            processed_item = self._process_agenda_item(
                                scraped_item_data, params['ID'], meeting_id, timestamp)
                            if processed_item is not None:
                                processed_agenda[current_section].append(
                                    processed_item)
        new_processed_agenda = self._combine_and_keep(
            processed_agenda, ["SPECIAL AGENDA ITEMS", "CONSENT CALENDAR", "STUDY SESSION", "CONTINUED ITEMS", "ADMINISTRATIVE PROCEEDINGS", "ORDINANCES", "STAFF ADMINISTRATIVE ITEMS", "PUBLIC HEARINGS"])
        return(new_processed_agenda)

    def _test_item(self, keeping):
        if not keeping["recommendations"]:
            return False
        if keeping["title"] is None:
            return False
        if not keeping["body"]:
            return False
        return True

    def _combine_and_keep(self, dictionary_agenda, keep):
        new_object = {
            "meeting_time": dictionary_agenda["meeting_time"],
            "meeting_id": dictionary_agenda["meeting_id"]
        }
        accumulator = []
        for keep_this in keep:
            kept = [keeping for keeping in dictionary_agenda[keep_this]
                    if self._test_item(keeping)]
            accumulator.extend(kept)
        if SCRAPER_VERBOSE_DEBUG:
            log.error(accumulator)
        new_object["items"] = accumulator
        return new_object

    def _scrape_agenda_item(self, agenda_item_location):
        return bs4_data_from_url(agenda_item_location, self._session, 'GET')

    def _get_department_sponsors(self, info_section_data):
        table_body = info_section_data.find('table')
        if table_body is not None:
            table_row = table_body.find('tr')  # Just find first!
            if table_row is not None:
                td_children = table_row.find_all('td')
                department = td_children[0].get_text().replace(
                    '&amp;', 'and').strip()
                sponsors = td_children[1].get_text().strip()
                if sponsors == '':
                    sponsors = None
                if department == '':
                    department = None
            else:
                return None, None
        return department, sponsors

    def _process_recommendations(self, recommendations_data):
        recommendations = []
        # font-family:Arial; font-size:12pt is recommendations
        # Span's not equal to just &nbsp
        # Span where not [0-9]+.
        recommended_action_re = re.compile(
            r"(^Recommended Actions?\W*:$)|(^Recommendation\W*$)?", re.RegexFlag.IGNORECASE)
        ps = recommendations_data.find_all('p')
        list_actions = recommendations_data.find('ol')
        if list_actions is not None:
            # preferred method
            next = list_actions.find('li')
            while next is not None:
                if next.name == 'ol':
                    recommendations[-1] += " "+unicodedata.normalize(
                        "NFKD", next.get_text()).strip()
                else:
                    recommendations.append(" "+unicodedata.normalize(
                        "NFKD", next.get_text().strip()))
                next = next.next_sibling
        else:
            for p in ps:
                current_recommendation = ""
                p_text = unicodedata.normalize("NFKD", p.get_text())
                if recommended_action_re.search(p_text):
                    continue
                p_text = SPACE_REGEX.sub(" ", p_text)
                p_text = ITEM_REGEX.sub("", p_text)
                if EMPTY_REGEX.search(p_text) or p_text == "":
                    continue
                recommendations.append(p_text.strip())
        return recommendations

    def _process_span(self, span):
        processed_span = SPACE_REGEX.sub(' ', span)
        processed_span = DOT_REGEX.sub("", processed_span)
        return processed_span

    def _process_spans(self, spans):
        """
        spans are normalized but not processed. Here, determine how one span should be connected to another
        """
        if len(spans) == 0:
            return ""
        processed_spans = "".join([self._process_span(span) for span in spans])
        return processed_spans

    def _process_body(self, body_data):
        processed_body = []
        outerdiv = body_data.find('div')
        innerdiv = outerdiv.find('div')
        body_paragraphs = innerdiv.find_all('p', recursive=False)
        for body_paragraph in body_paragraphs:
            if SCRAPER_VERBOSE_DEBUG:
                log.error(body_paragraph.get_text())
        for p in body_paragraphs:
            spans = p.find_all('span')
            spans_normalized = [unicodedata.normalize("NFKD", span.get_text()) for span in spans if not (
                span.attrs["style"] and check_style_special(span.attrs["style"]))]
            processed_body.append(self._process_spans(spans_normalized))
        return processed_body

    def _process_agenda_item(self, agenda_item_data, agenda_item_id, meeting_id, meeting_time):
        processed_item = {
            "title": None,
            "department": None,
            "body": [],
            "recommendations": [],
            "sponsors": None,
            "meeting_time": meeting_time,
            "agenda_item_id": agenda_item_id,
            "meeting_id": meeting_id,
            "tags": []
        }

        # Items must have a title!
        title = agenda_item_data.find(
            'h1', {'id': 'ContentPlaceholder1_lblLegiFileTitle'})
        if not title:
            return None
        processed_item['title'] = title.get_text().strip()

        # Items MAY have an info section
        info = agenda_item_data.find('div', {'class': 'LegiFileInfo'})
        if info is not None:
            info_body = info.find('div', {'class': 'LegiFileSectionContents'})
            department, sponsors = self._get_department_sponsors(info_body)
            processed_item['department'] = department
            processed_item['sponsors'] = sponsors

        # Items should have a recommended items section
        recommendations_body = agenda_item_data.find(
            'div', {'id': 'divItemDiscussion'})
        if recommendations_body is not None:
            processed_item['recommendations'] = self._process_recommendations(
                recommendations_body)

        # We only take items with a body now
        body = agenda_item_data.find('div', {'id': 'divBody'})

        if body is not None:
            processed_item["body"] = self._process_body(body)

        if not processed_item["body"] and not processed_item["recommendations"]:
            return None  # Will not capture items with no body and no recommendations
        return processed_item

    def _store_agenda(self, processed_agenda):
        session = self._DBsession()
        seconds_delta_for_pdf = 5 * 60  # 5 minutes post cutoff
        dt = datetime.fromtimestamp(processed_agenda["meeting_time"])
        dt_local = dt.astimezone(tz=self._tz)
        dt_local = dt_local.replace(hour=self._Committee.cutoff_hour,
                                    minute=self._Committee.cutoff_minute)
        dt_cutoff = dt_local + \
            timedelta(days=self._Committee.cutoff_offset_days)
        cutoff_timestamp = dt_cutoff.timestamp()
        pdf_timestamp = cutoff_timestamp + seconds_delta_for_pdf
        stored_agenda = Agenda(
            meeting_time=processed_agenda["meeting_time"],
            committee_id=self._Committee.id,
            meeting_id=processed_agenda["meeting_id"],
            cutoff_time=int(cutoff_timestamp),
            pdf_time=int(pdf_timestamp))
        session.add(stored_agenda)
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            log.error(
                "Something happened when adding agenda {}: {}".format(processed_agenda["meeting_id"], str(exc)))
        return stored_agenda

    def _store_agenda_items(self, agenda_dict, agenda_saved):
        session = self._DBsession()
        try:
            for item in agenda_dict["items"]:
                try:
                    new_agenda_item = AgendaItem(
                        title=item["title"],
                        department=item["department"],
                        body=item["body"],
                        sponsors=item["sponsors"],
                        agenda_id=agenda_saved.id,
                        meeting_time=item["meeting_time"],
                        agenda_item_id=item["agenda_item_id"]
                    )
                    session.add(new_agenda_item)
                    session.commit()
                    # need id so must commit before next add
                    self._store_agenda_reccommendations(
                        item["recommendations"], new_agenda_item, session)

                    # load item to elasticsearch
                    if ES_ENABLED:
                        es_item = {
                            'date': item["meeting_time"],
                            'agenda_item_id': item["agenda_item_id"],
                            'agenda_id': agenda_saved.id,
                            'title': item["title"],
                            'recommendations': item["recommendations"],
                            'body': item["body"],
                            'department': item["department"],
                            'sponsors': item["sponsors"],
                            'tags': None,
                            'committee': self._Committee.name,
                            'committee_id': self._Committee.id,
                        }

                        es_load = self._elasticsearch_utility.postItem(es_item)
                        if SCRAPER_DEBUG:
                            log.info(es_load)
                except Exception as itemExc:
                    agendaitem = item["agenda_item_id"]
                    log.error(
                        f"Could not add item {agendaitem} with {itemExc}")
        except Exception as exc:
            log.error(
                "Something happened when adding agenda items from agenda {}: {}".format(agenda_saved.id, str(exc)))
            session.rollback()

    def _store_agenda_reccommendations(self, recommendations, agenda_item, session):
        session.add(AgendaRecommendation(
            agenda_item_id=agenda_item.id, recommendation=recommendations))
        session.commit()
        # Commit the recommendations for the item
