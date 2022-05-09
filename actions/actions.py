# This files contains your custom actions which can be used to run
# custom Python code.
#
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from collections import defaultdict
from wsgiref.validate import InputWrapper
import requests
import urllib
import logging

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from utils import medias_synonyms as medias


ENDPOINT = "http://graphdb.sparna.fr/repositories/philharmonie-chatbot?query="
VOICE_CHANNELS = ["google_assistant", "alexa"]

class NoEntityFoundException(Exception):
    pass


class ActionGetSheetMusicByCasting(Action):
    def __init__(self):
        super(ActionGetSheetMusicByCasting, self).__init__()
        self.route_prefix = "PREFIX dc: <http://purl.org/dc/elements/1.1/> PREFIX dct: <http://purl.org/dc/terms/> PREFIX mus: <http://data.doremus.org/ontology#> PREFIX ecrm: <http://erlangen-crm.org/current/> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> PREFIX owl: <http://www.w3.org/2002/07/owl#> PREFIX foaf: <http://xmlns.com/foaf/0.1/> select ?score ?scoreUrl  ?scoreLabel ?responsibilityLabel where { "
        self.route_suffix = "?score mus:U170_has_title_statement ?scoreLabelStatement. ?scoreLabelStatement rdfs:label ?scoreLabel. optional {?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title.  ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel} bind (strafter(str(?score),\"ark/49250/\")as ?identifier) BIND(IRI(CONCAT(\"https://catalogue.philharmoniedeparis.fr/doc/ALOES/\", ?identifier)) AS ?scoreUrl1) BIND ( substr(str(?scoreUrl1), 1, 58) as ?scoreUrl) } Limit 20"
        self.allowed_medias = list(medias.iaml.keys()) + list(medias.mimo.keys())

    def name(self) -> Text:
        return "action_get_sheet_music_by_casting"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message['entities']
        logging.info(entities)
        answer =    f"Il me semble que vous voulez obtenir une liste des partitions. "
        try:
            inputted_medias = dict()
            for i, ent in enumerate(entities):
                key = ent.get('value')
                if ent['entity'] == 'medium' and key not in inputted_medias:
                    if i > 0 and entities[i-1]['entity'] == 'number':
                        inputted_medias[key] = entities[i-1].get('value')
                    else:
                        inputted_medias[key] = 1
            # if inputted_medias is None, empty, or contains no key of medias.medias, throw error
            if not inputted_medias or not set(inputted_medias.keys()).issubset(self.allowed_medias):
                raise NoEntityFoundException(f"Problem with entities: {inputted_medias}")
            results, formatted_mediums = self.get_query_results(inputted_medias)
            if not results:
                raise Exception(f"No results found for medias: {inputted_medias}")
            formatted_results = "\n".join(results)
            answer += f" Voici les partitions avec {formatted_mediums}:\n"
            answer += formatted_results
        except Exception:
            answer += "Mais je n'ai pas trouvé de résultats pour votre recherche. Veuillez reformuler votre question svp."
        dispatcher.utter_message(text=answer)
        return []

    def get_query_results(self, inputted_medias: dict) -> List[str]:
        formatted_query, formatted_mediums = self.format_sparql_query(inputted_medias)
        route = ENDPOINT + formatted_query
        logging.info(f"Requesting {route}")
        results = requests.get(route, headers={'Accept': 'application/sparql-results+json'}).json()
        texts = []
        for res in results["results"]["bindings"]:
            url = res["score"]["value"]
            title = res["scoreLabel"]["value"]
            texts.append(f"- [{title}]({url})")
        return texts, formatted_mediums

    def format_sparql_query(self, inputted_medias: dict) -> str:
        values, query = "?score mus:U13_has_casting ?casting . ", ""
        formatted_mediums = ""
        for i, medium in enumerate(inputted_medias.keys()):
            # Check if mimo or iaml
            if medium.isdigit():
                formatted_medium = f"<http://www.mimo-db.eu/InstrumentsKeywords/{medium}>"
                formatted_mediums += f"{inputted_medias[medium]} {medias.mimo[medium][0]}"
            else:
                formatted_medium = f"<http://data.doremus.org/vocabulary/iaml/mop/{medium}>"
                formatted_mediums += f"{inputted_medias[medium]} {medias.iaml[medium][0]}"
            if i == len(inputted_medias) - 2:
                formatted_mediums += " et "
            elif i < len(inputted_medias) - 2:
                formatted_mediums += ", "
            count = inputted_medias[medium]
            values += f"values (?input_quantity_{i} ?input_medium_{i}) {{ (\"{count}\"^^xsd:integer {formatted_medium})}}"
            query += f"?score mus:U13_has_casting ?casting . ?casting mus:U23_has_casting_detail ?castingDetail_{i}. ?castingDetail_{i} mus:U2_foresees_use_of_medium_of_performance ?input_medium_{i} . ?castingDetail_{i} mus:U30_foresees_quantity_of_mop ?input_quantity{i} ."
        parsed_query = urllib.parse.quote(self.route_prefix + values + query + self.route_suffix)
        return parsed_query, formatted_mediums
