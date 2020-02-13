import requests
import os
import json

ES_INDEX_NAME = os.environ.get('ES_INDEX_NAME', 'agenda_items')
ES_ENPOINT_NAME = os.environ.get('ES_ENDPOINT_NAME', 'es01')

class ElasticsearchUtility():
    @staticmethod
    def loadItems(items=None):
        """
        helper function to load scrapped agenda item to elastic search

            Args: 
                items: dict, key/value pairs representing elasticseaech index fileds. The accepted
                        keys are:
                            - date: date, meeting date
                            - agenda_item_id: int, agenda item id
                            - agenda_id: int, the id of the specific meeting
                            - title: str, the title of the agenda
                            - recommendations: str, the propposed recommendation from the city
                            - body: str, details about the items
                            - department: list, all departments concerned with the item
                            - sponsors: str,
                            - tags: None
                            - committee: str, the name of the comittee,
                            - committee_id: int, the id of the comitte
            Returns:
                str, 
        """

        url = f'http://{ES_ENPOINT_NAME}:9200/{ES_INDEX_NAME}/_doc/'

        payload = {
            'date': items.get('date'),
            'agenda_item_id': int(items.get('agenda_item_id')),
            'agenda_id': items.get('agenda_id'),
            'title': items.get('title'),
            'recommendations': items.get('recommendations'),
            'body': items.get('body'),
            'department': items.get('department').split(','),
            'sponsors': items.get('sponsors'),
            'tags': items.get('tags'),
            'committee': items.get('committee'),
            'committee_id': items.get('committee_id'),
        }

        r = requests.post(url, json=payload)
        response = json.loads(r.text)

        if not response.get('_shards'):
            err = response.get("error")
            return f"Failed to load 1 agenda item.\nerror: {err}"
        else:
            index, id = response.get('_index'), response.get('_id')
            return f"Loaded 1 agenda item in elasticsearch index {index}, with document id {id}"