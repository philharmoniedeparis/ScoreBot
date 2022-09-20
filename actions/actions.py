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

from fuzzywuzzy import fuzz
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from utils import medias_synonyms as medias
from utils import levels_synonyms as levels
from utils import genres_synonyms as genres
from utils import agents_synonyms as agents


ENDPOINT = "http://graphdb.sparna.fr/repositories/philharmonie-chatbot?query="
VOICE_CHANNELS = ["google_assistant", "alexa"]

class NoEntityFoundException(Exception):
    pass


class ActionGetSheetMusicByCasting(Action):
    def __init__(self):
        super(ActionGetSheetMusicByCasting, self).__init__()
        self.route = """ 
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX mus: <http://data.doremus.org/ontology#>
PREFIX ecrm: <http://erlangen-crm.org/current/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX phil: <https://data.philharmoniedeparis.fr/>
PREFIX philhar: <http://data.philharmoniedeparis.fr/ontology/partitions#>

select distinct ?score ?identifier ?scoreUrl  ?scoreTitleLabel ?genrelabel ?responsibilityLabel ?educationLevelLabel ?agent ?agentLabel ?roleLabel ?input_quantity_total 

where {{
    {filters}
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .

# les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
# ... et on veut récupérer tous les instruments du casting 
    ?casting mus:U23_has_casting_detail ?castingDetail .
    ?castingDetail philhar:P1_foresees_use_of_medium_of_performance_instrument ?medium.
    ?medium skos:prefLabel ?mediumLabel.
    filter (lang(?mediumLabel)="fr")
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(IRI(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", ?identifier)) AS ?scoreUrl1)
    BIND ( substr(str(?scoreUrl1), 1, 58) as ?scoreUrl)
}}
        """
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
            level, genre, agent = None, None, None
            for i, ent in enumerate(entities):
                key = ent.get('value')
                if ent['entity'] == 'medium' and key not in inputted_medias:
                    if i > 0 and entities[i-1]['entity'] == 'number':
                        inputted_medias[key] = entities[i-1].get('value')
                    else:
                        inputted_medias[key] = 1

                if ent['entity'] == 'level' and level is None:
                    level = ent.get("value")
                if ent['entity'] == 'genre' and genre is None:
                    genre = ent.get("value")
                if ent['entity'] == 'agent' and agent is None:
                    agent = ent.get("value")

            # if inputted_medias is None, empty, or contains no key of medias.medias, throw error
            if inputted_medias and not set(inputted_medias.keys()).issubset(self.allowed_medias):
                raise NoEntityFoundException(f"Problem with entities: {inputted_medias}")

            logging.info(f"level: {level}, genre: {genre}, agent: {agent}")
            if level is not None and level not in levels.all_levels:
                level, level_name = self.get_closest_event(level, levels.all_levels)
                logging.info(level)
            if genre is not None and genre not in genres.genres:
                genre, genre_name = self.get_closest_event(genre, genres.genres)
                logging.info(genre)
            if agent is not None and agent not in agents.agents:
                agent, agent_name = self.get_closest_event(agent, agents.agents)
                logging.info(agent)

            results, formatted_mediums = self.get_query_results(inputted_medias, level, genre, agent)
            if not results:
                raise Exception(f"No results found for medias: {inputted_medias}")
            formatted_results = "\n".join(results)
            answer += f" Voici les partitions avec {formatted_mediums}:\n"
            answer += formatted_results
        except Exception:
            answer += "Mais je n'ai pas trouvé de résultats pour votre recherche. Veuillez reformuler votre question svp."
        dispatcher.utter_message(text=answer)
        return []

    def get_query_results(self, inputted_medias: dict, level, genre, agent) -> List[str]:
        formatted_query, formatted_mediums = self.format_sparql_query(inputted_medias, level, genre, agent)
        route = ENDPOINT + formatted_query
        logging.info(f"Requesting {route}")
        results = requests.get(route, headers={'Accept': 'application/sparql-results+json'}).json()
        texts = []
        for res in results["results"]["bindings"][:20]:
            url = res["scoreUrl"]["value"]
            title = res["scoreTitleLabel"]["value"]
            texts.append(f"- [{title}]({url})")
        return texts, formatted_mediums

    def format_sparql_query(self, inputted_medias: dict, level: str, genre: str, agent: str) -> str:
        filters = ""
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

            # Medium
            filters += f"""
values (?input_quantity_{i} ?input_medium_{i}) {{ (\"{count}\"^^xsd:integer {formatted_medium})}}
?input_medium_{i} skos:narrower* ?input_medium_{i}_list.
?casting mus:U23_has_casting_detail ?castingDetail_{i}.
?castingDetail_{i} philhar:P1_foresees_use_of_medium_of_performance_instrument ?input_medium_{i}_list.
?castingDetail_{i} mus:U30_foresees_quantity_of_mop ?input_quantity_{i} .
            """
            
        logging.info(f"level: {level}, genre: {genre}, agent: {agent}")
        # Level
        if level is not None:
            filters += f"""
values (?input_educational_level) {{ (<https://data.philharmoniedeparis.fr/vocabulary/edudational-level/{level}>)}}
?castingDetail ecrm:P103_was_intended_for ?input_educational_level.
?input_educational_level skos:prefLabel ?educationLevelLabel.
            """
        # Genre
        if genre is not None:
            filters += f"""
values (?input_genre ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/00{genre}>)}}
?score mus:U12_has_genre ?input_genre.
?input_genre skos:prefLabel ?genrelabel.
            """
        
        # Agent
        if agent is not None:
            filters += f"""
values (?input_agent_role ?input_agent ) {{ (<http://data.bnf.fr/vocabulary/roles/r220/> <https://ark.philharmoniedeparis.fr/ark:49250/00{agent}>) }}
?creation  mus:R24_created ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by ?input_agent.
?task mus:U31_had_function ?input_agent_role.
?input_agent_role skos:prefLabel ?roleLabel.
filter (lang(?roleLabel)=\"fr\")
?input_agent rdfs:label ?agentLabel.
"""

        parsed_query = urllib.parse.quote(self.route.format(filters=filters))
        return parsed_query, formatted_mediums

    def get_closest_event(self, value: str, candidates: Dict = None):
        # Use fuzz ratio to compare value to the candidates in the dictionary
        # Return highest match
        closest_match = None
        closest_match_ratio = 70
        for key in candidates:
            for cand in candidates[key]:
                ratio = fuzz.ratio(value, cand)
                if ratio > closest_match_ratio:
                    closest_match = key
                    closest_match_ratio = ratio
        if closest_match is None:
            return None, None
        return closest_match, candidates[closest_match][0]
