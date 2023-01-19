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
from collections import defaultdict
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
DEBUG = True if GRAPHDB_DOMAIN == "http://graphdb.sparna.fr" else False
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


select distinct ?score ?scoreResearch ?snippetField ?snippetText ?identifier ?scoreUrl  ?scoreTitleLabel ?genrelabel ?responsibilityLabel ?educationLevelLabel ?agent ?agentLabel ?roleLabel ?input_quantity_total ?compositeurLabel

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
        worded_mediums = ""
        results = []
        try:
            inputted_medias = dict()
            entity_dict = defaultdict(lambda: defaultdict(lambda: None))
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
                            inputted_medias[medium] = int(volume)
                        else:
                            inputted_medias[medium] = 1

                if ent['entity'] == 'level' and entity_dict["level"]["code"] is None:
                    level = ent.get("value")
                    if level not in levels.all_levels:
                        level, level_name = self.get_closest_event(level, levels.all_levels)
                        logging.info(f"Parsed level: {level}")
                    entity_dict["level"] = {'code': level, 'name': levels.all_levels.get(level, [None])[0]}

                if ent['entity'] == 'formation' and entity_dict["formation"]["code"] is None:
                    formation = ent.get("value")
                    if formation not in formations.formations:
                        formation, formation_name = self.get_closest_event(formation, formations.formations)
                        logging.info(f"Parsed formation: {formation}")
                    # Is the formation the total number of instruments OR a specific medium count?
                    j = i
                    while j < len(entities) - 1:
                        # If there is a number between formation and the next medium, then formation is the total
                        if entities[j]['entity'] == 'number':
                            break
                        # Else if there's a medium directly after, then formation is just this medium's count 
                        elif entities[j]['entity'] == 'medium':
                            formation = None
                            break
                        j += 1
                    entity_dict["formation"] = {'code': formation, 'name': formations.formations.get(formation, [None, None])[1]}


                if ent['entity'] == 'genre' and entity_dict["genre"]["code"] is None:
                    genre = ent.get("value")
                    if genre.isdigit() and genre not in genres.genres:
                        entity_dict = self.reassign_type(genre, entity_dict)
                    else:
                        if genre not in genres.genres:
                            genre, genre_name = self.get_closest_event(genre, genres.genres)
                            logging.info(f"Parsed genre: {genre}")
                        entity_dict["genre"] = {'code': genre, 'name': genres.genres.get(genre, [None])[0]}

                if ent['entity'] == 'agent' and entity_dict["agent"]["code"] is None:
                    agent = ent.get("value")
                    if agent.isdigit() and agent not in agents.agents:
                        entity_dict = self.reassign_type(agent, entity_dict)
                    else:
                        if agent not in agents.agents:
                            agent, agent_name = self.get_closest_event(agent, agents.agents)
                            logging.info(f"Parsed agent: {agent}")
                        entity_dict["agent"] = {'code': agent, 'name': agents.agents.get(agent,[None])[0]}

                if ent['entity'] == 'period' and entity_dict["period"]["code"] is None:
                    period = ent.get("value")
                    if period.isdigit() and period not in periods.periods:
                        entity_dict = self.reassign_type(period, entity_dict)
                    else:
                        if period not in periods.periods:
                            period, period_name = self.get_closest_event(period, periods.periods)
                            logging.info(f"Parsed period: {period}")
                        entity_dict["period"] = {'code': period, 'name': periods.periods.get(period,[None])[0]}
                        
                if ent['entity'] == 'location' and entity_dict["location"]["code"] is None:
                    location = ent.get("value")
                    if location.isdigit() and location not in locations.locations:
                        entity_dict = self.reassign_type(location, entity_dict)
                    else:
                        if location not in locations.locations:
                            location, location_name = self.get_closest_event(location, locations.locations)
                            logging.info(f"Parsed location: {location}")
                        entity_dict["location"] = {'code': location, 'name': locations.locations.get(location, [None])[0]}
    
                if ent['entity'] == 'work_name' and entity_dict["work_name"]["code"] is None:
                    work_name = ent.get("value")
                    if work_name.isdigit():
                        entity_dict = self.reassign_type(work_name, entity_dict)
                    else:
                        entity_dict["work_name"] = {'code': work_name, 'name': work_name}

            # if inputted_medias is None, empty, or contains no key of medias.medias, throw error
            if inputted_medias and not set(inputted_medias.keys()).issubset(self.allowed_medias):
                raise NoEntityFoundException(f"Problem with entities: {inputted_medias}")

            logging.info(f"medium: {inputted_medias}, entity_dict: {entity_dict}")

            results, worded_mediums = self.get_query_results(inputted_medias, entity_dict, exclusive=True)
            if not results:
                results, worded_mediums = self.get_query_results(inputted_medias, entity_dict)
                if results:
                    answer += "Je n'ai pas trouvé de résultats comportant uniquement l'instrumentation que vous avez spécifié, j'ai donc élargi la recherche aux partitions comportant également d'autres instruments.\n"
                else:
                    raise NoResultsException(f"No results found for medias: {inputted_medias}")

            formatted_results = "\n".join(results)
            answer += self.add_results_and_criterias(results, entity_dict, worded_mediums, formatted_results=formatted_results)
        except Exception:
            logging.info(traceback.print_exc())
            answer += "Mais je n'ai pas trouvé de résultats"
            answer += self.add_results_and_criterias(None, entity_dict, worded_mediums)
        dispatcher.utter_message(text=answer)
        return []

    def get_query_results(self, inputted_medias: dict, entity_dict: dict, exclusive=False) -> List[str]:
        formatted_query, worded_mediums = self.format_sparql_query(inputted_medias, entity_dict, exclusive)
        route = ENDPOINT + formatted_query
        logging.info(f"Requesting {route}")
        results = requests.get(route, headers={'Accept': 'application/sparql-results+json', 'Authorization': TOKEN}).json()
        texts = []
        for res in results["results"]["bindings"][:MAX_RESULTS_TOTAL]:
            url = res["scoreUrl"]["value"]
            title = res["scoreTitleLabel"]["value"]
            compositeur = res["compositeurLabel"]["value"]
            if DEBUG and entity_dict["work_name"]["code"] is not None:
                score = res.get("scoreResearch", {}).get("value", "")
                try:
                    score = str(round(float(score), 2))
                except:
                    score = ""
                texts.append(f"- {f'[{score}]'} [{title}]({url}), {compositeur}")
            else:
                texts.append(f"- [{title}]({url}), {compositeur}")
        return texts, worded_mediums

    def format_sparql_query(self, inputted_medias: dict, entity_dict: dict, exclusive: bool) -> str:
        filters = ""
        worded_mediums = ""

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
?castingDetail_{i} mus:U30_foresees_quantity_of_mop ?input_quantity_{i} .
# If we have a parent instrument (skos:narrower*), check that some children are contained by the score's casting
FILTER EXISTS {{
    # Get all the instruments of the score's casting
    ?castingDetail_{i} philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?casting_instrument.
    # Check that some casting_instruments are in score's casting
    ?input_medium_{i}  skos:narrower* ?casting_instrument.
}}
            """
            
        #calculer la quantité totale d'instruments
        if exclusive and inputted_medias:
            if entity_dict["formation"]["code"] is not None:
                total = entity_dict["formation"]["code"]
            else:
                total = sum(inputted_medias.values())
            filters += f"""
values (?input_quantity_total) {{(\"{total}\"^^xsd:integer)}}
?casting mus:U48_foresees_quantity_of_actors ?input_quantity_total.
            """

        # Level
        if entity_dict["level"]["code"] is not None:
            filters += f"""
values (?input_educational_level) {{ (<https://data.philharmoniedeparis.fr/vocabulary/edudational-level/{entity_dict["level"]["code"]}>)}}
?castingDetail ecrm:P103_was_intended_for ?input_educational_level.
?input_educational_level skos:prefLabel ?educationLevelLabel.
            """
        # Genre
        if entity_dict["genre"]["code"] is not None:
            while len(entity_dict["genre"]["code"]) < 7:
                entity_dict["genre"]["code"] = "0" + entity_dict["genre"]["code"]
            filters += f"""
values (?input_genre ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["genre"]["code"]}>)}}
?score mus:U12_has_genre ?input_genre.
?input_genre skos:prefLabel ?genrelabel.
            """
        
        # Agent
        if entity_dict["agent"]["code"] is not None:
            while len(entity_dict["agent"]["code"]) < 7:
                entity_dict["agent"]["code"] = "0" + entity_dict["agent"]["code"]
            filters += f"""
values (?input_agent_role ?input_agent ) {{ (<http://data.bnf.fr/vocabulary/roles/r220/> <https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["agent"]["code"]}>) }}
?creation  mus:R24_created ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by ?input_agent.
?task mus:U31_had_function ?input_agent_role.
?input_agent_role skos:prefLabel ?roleLabel.
filter (lang(?roleLabel)=\"fr\")
?input_agent rdfs:label ?agentLabel.
"""

        if entity_dict["period"]["code"] is not None:
            while len(entity_dict["period"]["code"]) < 7:
                entity_dict["period"]["code"] = "0" + entity_dict["period"]["code"]
            filters += f"""
values (?input_period ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["period"]["code"]}>)}}
?score mus:U52_has_context ?input_period.
?input_period skos:prefLabel ?categorieLabel.
"""


        if entity_dict["work_name"]["code"] is not None:
            lucene_query = " AND ".join([word + "~0.6" for word in entity_dict["work_name"]["code"].split(" ")])
            logging.info(lucene_query)
            filters += f"""
values (?classes ) {{ (efrbroo:F24_Publication_Expression)(mus:M167_Publication_Expression_Fragment)}} 
?search a luc-index:TitleIndex ;
    luc:query "{lucene_query}" ;  
    luc:entities ?score .
    ?score a ?classes.
    ?score luc:score ?scoreResearch .
    ?score luc:snippets ?snippet .
    ?snippet luc:snippetField ?snippetField ;
    luc:snippetText ?snippetText .
"""

        if entity_dict["location"]["code"] is not None:
            while len(entity_dict["location"]["code"]) < 7:
                entity_dict["location"]["code"] = "0" + entity_dict["location"]["code"]
            filters += f"""
values (?localisation) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["location"]["code"]}>) }}
?score mus:U65_has_geographical_context ?localisation.
?localisation skos:prefLabel ?localisationLabel.
"""

        # Display compositeurLabel for easier reading of the results
        filters += f"""
        #avoir le compositeur de l’oeuvre
?creation  mus:R24_created   ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by ?compositeur.
?task mus:U31_had_function <http://data.bnf.fr/vocabulary/roles/r220/>.
?compositeur rdfs:label ?compositeurLabel.
"""

        parsed_query = urllib.parse.quote_plus(self.route.format(filters=filters, limit=MAX_RESULTS_TOTAL), safe='/')
        return parsed_query, worded_mediums

    def get_closest_event(self, value: str, candidates: Dict = None):
        # Use fuzz ratio to compare value to the candidates in the dictionary
        # Return highest match
        closest_match = None
        closest_match_ratio = 81
        for key in candidates:
            for cand in candidates[key]:
                ratio = fuzz.ratio(value, cand)
                if ratio > closest_match_ratio:
                    print(value, cand)
                    closest_match = key
                    closest_match_ratio = ratio
        if closest_match is None:
            return None, None
        return closest_match, candidates[closest_match][0]

    def reassign_type(self, entity_code, entity_dict):
        authorized_values = {
            "genre": genres.genres, 
            "agent": agents.agents,
            "period": periods.periods,
            "location": locations.locations
        }
        for entity_type, authorized in authorized_values.items():
            if entity_code in authorized:
                entity_dict[entity_type]["code"] = entity_code
                entity_dict[entity_type]["name"] = authorized[entity_code][0]
                return entity_dict
        return entity_dict

    def add_results_and_criterias(self, results, entity_dict, worded_mediums, formatted_results=None):
        def add_criterias(entity_dict):
            res = ""
            criterias = [val["name"] for val in entity_dict.values() if val["name"] is not None]
            if worded_mediums: 
                criterias += [worded_mediums]
            if criterias:
                res += f" pour les critères" if len(criterias) > 1 else f" pour le critère"
                for i, entity_name in enumerate(criterias):
                    res += f" {entity_name}"
                    if i < len(criterias) - 2:
                        res += ","
                    elif i == len(criterias) - 2:
                        res += " et"
            return res
        worded_criterias = add_criterias(entity_dict)

        worded_results = ""
        if formatted_results:
            worded_results += f"Voici les "
            if len(results) >= MAX_RESULTS_TOTAL:
                worded_results += f"{len(results)} premières "
            worded_results += "partitions que j'ai trouvées"
            worded_results += worded_criterias
            worded_results += f":\n{formatted_results}"
        else:
            worded_results += f"{worded_criterias}."

        return worded_results
