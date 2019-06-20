from abc import ABC, abstractmethod, abstractproperty
from pytz import timezone

class EngageScraper(ABC):
    def __init__(self, base_agenda_location, tz_string):
        super().__init__()
        self._agenda_locations = []
        self._base_agenda_location = base_agenda_location
        self._tz = timezone(tz_string)

    def _get_agenda_locations(self):
        self._agenda_locations

    def _set_agenda_locations(self, agenda_locations):
        self._agenda_locations = agenda_locations

    agenda_base_location = property(
        _get_agenda_locations, _set_agenda_locations, "The locations of the root of all agendas.")

    @abstractmethod
    def get_available_agendas(self):
        """
        Method to determine what agendas are available.
        Sets the self._agenda_locations property
        In a typical HTML scraper, these resources would be HTTP URLs
        """
        pass

    @abstractmethod
    def scrape(self):
        """
        Scrape processes all agendas in self._agenda_locations
        It calls process agenda on all items in _agenda_locations with 
        data downloaded from those locations.
        The result of scrape is the stored agendas and agenda items.
        """
        pass

    @abstractmethod
    def process_agenda(self, agenda_data, meeting_id):
        """
        process_agenda takes one agenda document (for instance HTML document) data.
        A processed agenda will have to process each of its items. Each agenda item might
        be at a different location or contained within an agenda. If they are contained within
        the agenda, progress to process_agenda_item with its data. If not, scrape_agenda_item should be
        called with the location of the agenda_item.
        The result of process agenda will be a dict that can be saved by store_agenda and store_agenda_items
        """
        pass

    @abstractmethod
    def scrape_agenda_item(self, agenda_item_location):
        """
        Takes a location and produces the data from the item and calls process_agenda_item
        """
        pass

    @abstractmethod
    def process_agenda_item(self, agenda_item_data, agenda_item_id, meeting_id, meeting_time):
        """
        The result of process agenda item will be a dict that can be stored by store_agenda_item
        """
        pass

    @abstractmethod
    def store_agenda(self, processed_agenda, committee):
        """
        Calls to DB should be here for the main agenda content
        """
        pass

    @abstractmethod
    def store_agenda_items(self, agenda_dict, agenda_saved):
        """
        Calls to the DB should be here for agenda item content
        """
        pass
