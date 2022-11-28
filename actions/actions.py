# This files contains your custom actions which can be used to run
# custom Python code.
#
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import urllib
import logging
import traceback
import os

from fuzzywuzzy import fuzz
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from utils import medias_synonyms as medias
from utils import levels_synonyms as levels
from utils import genres_synonyms as genres
from utils import agents_synonyms as agents
from utils import periods_synonyms as periods
from utils import locations_synonyms as locations
from utils import formations_synonyms as formations

# Get Gitlab variables
USERNAME = os.environ.get("GRAPHDB_USERNAME")
PASSWORD = os.environ.get("GRAPHDB_PASSWORD")
GRAPHDB_DOMAIN = os.environ.get("GRAPHDB_DOMAIN", "http://graphdb.sparna.fr")
MAX_RESULTS_TOTAL = 25

# Get GraphDB auth
try:
    AUTH_REQUEST = requests.post(f"{GRAPHDB_DOMAIN}/rest/login", headers={"Content-type": "application/json"}, json={"username":USERNAME, "password": PASSWORD}, timeout=10)
    TOKEN = AUTH_REQUEST.headers.get("Authorization")
except requests.exceptions.ConnectTimeout:
    TOKEN = ""
    logging.warning("Could not reach the GraphDB login endpoint. If this is the prod environment, the succeeding requests may fail.")

ENDPOINT = f"{GRAPHDB_DOMAIN}/repositories/philharmonie-chatbot?query="
VOICE_CHANNELS = ["google_assistant", "alexa"]

class NoResultsException(Exception):
    pass

class NoEntityFoundException(Exception):
    pass


class ActionGetSheetMusicByCasting(Action):
    def __init__(self):
        super(ActionGetSheetMusicByCasting, self).__init__()
        self.route = """ 
PREFIX luc: <http://www.ontotext.com/connectors/lucene#>
PREFIX luc-index: <http://www.ontotext.com/connectors/lucene/instance#>
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
PREFIX efrbroo: <http://erlangen-crm.org/efrbroo/>


select distinct ?score ?scoreResearch ?snippetField ?snippetText ?identifier ?scoreUrl  ?scoreTitleLabel ?genrelabel ?responsibilityLabel ?educationLevelLabel ?agent ?agentLabel ?roleLabel ?input_quantity_total 

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
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    ?medium skos:prefLabel ?mediumLabel.
    filter (lang(?mediumLabel)="fr")
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
order by desc (?scoreResearch)
limit {limit}
        """
        self.allowed_medias = list(medias.iaml.keys()) + list(medias.mimo.keys())

    def name(self) -> Text:
        return "action_get_sheet_music_by_casting"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = sorted(tracker.latest_message['entities'], key= lambda d: d['start'])
        logging.info(entities)
        answer =    f"Il me semble que vous voulez obtenir une liste des partitions.\n"
        try:
            inputted_medias = dict()
            entity_dict = {"level": None, "genre": None, "agent": None, "formation": None, "period": None, "location": None, "work_name": None} 
            for i, ent in enumerate(entities):
                if ent['entity'] == 'medium':
                    medium = ent.get("value")
                    if medium.isdigit() and medium not in self.allowed_medias:
                        entity_dict = self.reassign_type(medium, entity_dict)
                    else:
                        if medium not in self.allowed_medias:
                            medium, medium_name = self.get_closest_event(medium, {**medias.iaml, **medias.mimo})
                            if medium is None:
                                continue
                        # Check if the medium has been entered after a number or formation
                        if i > 0 and entities[i-1]['entity'] in ['number', 'formation']:
                            entity = entities[i-1]['entity']
                            volume = entities[i-1]['value']
                            if entity == 'formation' and not volume.isdigit():
                                volume, _ = self.get_closest_event(volume, formations.formations)
                            inputted_medias[medium] = volume
                        else:
                            inputted_medias[medium] = 1

                if ent['entity'] == 'level' and entity_dict["level"] is None:
                    level = ent.get("value")
                    if level not in levels.all_levels:
                        level, level_name = self.get_closest_event(level, levels.all_levels)
                        logging.info(f"Parsed level: {level}")
                    entity_dict["level"] = level

                if ent['entity'] == 'formation' and entity_dict["formation"] is None:
                    formation = ent.get("value")
                    if formation not in formations.formations:
                        formation, formation_name = self.get_closest_event(formation, formations.formations)
                        logging.info(f"Parsed formation: {formation}")
                    entity_dict["formation"] = formation

                if ent['entity'] == 'genre' and entity_dict["genre"] is None:
                    genre = ent.get("value")
                    if genre.isdigit():
                        entity_dict = self.reassign_type(genre, entity_dict)
                    else:
                        if genre not in genres.genres:
                            genre, genre_name = self.get_closest_event(genre, genres.genres)
                            logging.info(f"Parsed genre: {genre}")
                        entity_dict["genre"] = genre

                if ent['entity'] == 'agent' and entity_dict["agent"] is None:
                    agent = ent.get("value")
                    if agent.isdigit():
                        entity_dict = self.reassign_type(agent, entity_dict)
                    else:
                        if agent not in agents.agents:
                            agent, agent_name = self.get_closest_event(agent, agents.agents)
                            logging.info(f"Parsed agent: {agent}")
                        entity_dict["agent"] = agent

                if ent['entity'] == 'period' and entity_dict["period"] is None:
                    period = ent.get("value")
                    if period.isdigit():
                        entity_dict = self.reassign_type(period, entity_dict)
                    else:
                        if period not in periods.periods:
                            period, period_name = self.get_closest_event(period, periods.periods)
                            logging.info(f"Parsed period: {period}")
                        entity_dict["period"] = period
                        
                if ent['entity'] == 'location' and entity_dict["location"] is None:
                    location = ent.get("value")
                    if location.isdigit():
                        entity_dict = self.reassign_type(location, entity_dict)
                    else:
                        if location not in locations.locations:
                            location, location_name = self.get_closest_event(location, locations.locations)
                            logging.info(f"Parsed location: {location}")
                        entity_dict["location"] = location
    
                if ent['entity'] == 'work_name' and entity_dict["work_name"] is None:
                    work_name = ent.get("value")
                    if work_name.isdigit():
                        entity_dict = self.reassign_type(work_name, entity_dict)
                    else:
                        entity_dict["work_name"] = work_name

            # if inputted_medias is None, empty, or contains no key of medias.medias, throw error
            if inputted_medias and not set(inputted_medias.keys()).issubset(self.allowed_medias):
                raise NoEntityFoundException(f"Problem with entities: {inputted_medias}")

            logging.info(f"medium: {inputted_medias}, entity_dict: {entity_dict}")

            results, worded_mediums = self.get_query_results(inputted_medias, entity_dict)
            if not results:
                results, worded_mediums = self.get_query_results(inputted_medias, entity_dict, exclusive=True)
                if results:
                    answer += "Je n'ai pas trouvé de résultats comportant uniquement l'instrumentation que vous avez spécifié, j'ai donc élargi la recherche aux partitions comportant également d'autres instruments.\n"
                else:
                    raise NoResultsException(f"No results found for medias: {inputted_medias}")
            formatted_results = "\n".join(results)
            logging.info(len(results))
            answer += f"Voici les "
            if len(results) >= MAX_RESULTS_TOTAL:
                answer += f"{len(results)} premières "
            answer += "partitions que j'ai trouvées"
            if worded_mediums:
                answer += f" avec {worded_mediums}"
            answer += f":\n{formatted_results}"
        except NoResultsException as e:
            logging.info(str(e))
            answer += "Mais je n'ai pas trouvé de résultats pour votre recherche dans la base de données de la Philharmonie."
        except Exception:
            logging.info(traceback.print_exc())
            answer += "Mais je n'ai pas trouvé de résultats pour votre recherche. Veuillez reformuler votre question svp."
        dispatcher.utter_message(text=answer)
        return []

    def get_query_results(self, inputted_medias: dict, entity_dict: dict, exclusive=True) -> List[str]:
        formatted_query, worded_mediums = self.format_sparql_query(inputted_medias, entity_dict, exclusive)
        route = ENDPOINT + formatted_query
        logging.info(f"Requesting {route}")
        results = requests.get(route, headers={'Accept': 'application/sparql-results+json', 'Authorization': TOKEN}).json()
        texts = []
        for res in results["results"]["bindings"][:MAX_RESULTS_TOTAL]:
            url = res["scoreUrl"]["value"]
            title = res["scoreTitleLabel"]["value"]
            texts.append(f"- [{title}]({url})")
        return texts, worded_mediums

    def format_sparql_query(self, inputted_medias: dict, entity_dict: dict, exclusive: bool) -> str:
        filters = ""
        worded_mediums = ""
        total_quantity = []

        for i, medium in enumerate(inputted_medias.keys()):
            # Check if mimo or iaml

            if medium.isdigit():
                formatted_medium = f"<http://www.mimo-db.eu/InstrumentsKeywords/{medium}>"
                worded_mediums += f"{inputted_medias[medium]} {medias.mimo[medium][0]}"
            else:
                formatted_medium = f"<http://data.doremus.org/vocabulary/iaml/mop/{medium}>"
                worded_mediums += f"{inputted_medias[medium]} {medias.iaml[medium][0]}"

            if exclusive and i == len(inputted_medias) - 2:
                worded_mediums += " et "
            elif not exclusive and i == len(inputted_medias) - 1:
                worded_mediums += " et d'autres instruments"
            elif i < len(inputted_medias) - 1:
                worded_mediums += ", "

            count = inputted_medias[medium]

            # Medium
            filters += f"""
values (?input_quantity_{i} ?input_medium_{i}) {{ (\"{count}\"^^xsd:integer {formatted_medium})}}
?input_medium_{i} skos:narrower* ?input_medium_{i}_list.
?casting mus:U23_has_casting_detail ?castingDetail_{i}.
?castingDetail_{i} philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?input_medium_{i}_list.
?castingDetail_{i} mus:U30_foresees_quantity_of_mop ?input_quantity_{i} .
            """
            total_quantity.append(f"?input_quantity_{i}")
            
        #calculer la quantité totale d'instruments
        if total_quantity and exclusive:
            filters += f"""
BIND(({"+".join(total_quantity)}) AS ?input_quantity_total)
?casting mus:U48_foresees_quantity_of_actors ?input_quantity_total.
            """

        # Level
        if entity_dict["level"] is not None:
            filters += f"""
values (?input_educational_level) {{ (<https://data.philharmoniedeparis.fr/vocabulary/edudational-level/{entity_dict["level"]}>)}}
?castingDetail ecrm:P103_was_intended_for ?input_educational_level.
?input_educational_level skos:prefLabel ?educationLevelLabel.
            """
        # Genre
        if entity_dict["genre"] is not None:
            while len(entity_dict["genre"]) < 7:
                entity_dict["genre"] = "0" + entity_dict["genre"]
            filters += f"""
values (?input_genre ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["genre"]}>)}}
?score mus:U12_has_genre ?input_genre.
?input_genre skos:prefLabel ?genrelabel.
            """
        
        # Agent
        if entity_dict["agent"] is not None:
            while len(entity_dict["agent"]) < 7:
                entity_dict["agent"] = "0" + entity_dict["agent"]
            filters += f"""
values (?input_agent_role ?input_agent ) {{ (<http://data.bnf.fr/vocabulary/roles/r220/> <https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["agent"]}>) }}
?creation  mus:R24_created ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by ?input_agent.
?task mus:U31_had_function ?input_agent_role.
?input_agent_role skos:prefLabel ?roleLabel.
filter (lang(?roleLabel)=\"fr\")
?input_agent rdfs:label ?agentLabel.
"""

        if entity_dict["period"] is not None:
            while len(entity_dict["period"]) < 7:
                entity_dict["period"] = "0" + entity_dict["period"]
            filters += f"""
values (?input_categorie ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["period"]}>)}}
?score mus:U19_is_categorized_as ?input_categorie.
?input_categorie skos:prefLabel ?categorieLabel.
"""


        if entity_dict["work_name"] is not None:
            filters += f"""
values (?classes ) {{ (efrbroo:F24_Publication_Expression)(mus:M167_Publication_Expression_Fragment)}} 
?search a luc-index:TitleIndex ;
    luc:query "{entity_dict["work_name"]}" ;  
    luc:entities ?score .
    ?score a ?classes.
    ?score luc:score ?scoreResearch .
    ?score luc:snippets ?snippet .
    ?snippet luc:snippetField ?snippetField ;
    luc:snippetText ?snippetText .
"""

        if entity_dict["location"] is not None:
            while len(entity_dict["location"]) < 7:
                entity_dict["location"] = "0" + entity_dict["location"]
            filters += f"""
values (?localisation) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["location"]}>) }}
?score ecrm:P2_has_type ?localisation.
?localisation skos:prefLabel ?localisationLabel.
"""

        parsed_query = urllib.parse.quote_plus(self.route.format(filters=filters, limit=MAX_RESULTS_TOTAL), safe='/')
        return parsed_query, worded_mediums

    def get_closest_event(self, value: str, candidates: Dict = None):
        # Use fuzz ratio to compare value to the candidates in the dictionary
        # Return highest match
        closest_match = None
        closest_match_ratio = 71
        for key in candidates:
            for cand in candidates[key]:
                cand = cand.lower()
                ratio = fuzz.ratio(value, cand)
                if ratio > closest_match_ratio:
                    print(value, cand)
                    closest_match = key
                    closest_match_ratio = ratio
        if closest_match is None:
            return None, None
        return closest_match, candidates[closest_match][0]

    def reassign_type(self, entity, entity_dict):
        authorized_values = {
            "genre": genres.genres, 
            "agent": agents.agents,
            "period": periods.periods,
            "location": locations.locations
        }
        for entity_type, authorized in authorized_values.items():
            if entity in authorized:
                entity_dict[entity_type] = entity
                return entity_dict
        return entity_dict
    # def reassign_type(self, entity, expected_authorized_values, value):
    #     authorized_values = [genres.genres, agents.agents, periods.periods, locations.locations]
    #     if entity.isdigit() and entity not in expected_authorized_values:
    #         for values in authorized_values:
    #             if entity in values: 
