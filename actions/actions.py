# This files contains your custom actions which can be used to run
# custom Python code.
#
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import ast
import requests
import urllib
import logging
import traceback
import os

from fuzzywuzzy import fuzz
from collections import defaultdict
from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
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
    AUTH_REQUEST = requests.post(
        f"{GRAPHDB_DOMAIN}/rest/login",
        headers={"Content-type": "application/json"},
        json={"username": USERNAME, "password": PASSWORD},
        timeout=10,
    )
    TOKEN = AUTH_REQUEST.headers.get("Authorization")
    # Check that we're connected and that the token is not empty
    if not TOKEN:
        logging.warning(
            "Could not get a valid token from GraphDB. If this is the prod environment, the succeeding requests may fail."
        )
except requests.exceptions.ConnectTimeout:
    TOKEN = ""
    logging.warning(
        "Could not reach the GraphDB login endpoint. If this is the prod environment, the succeeding requests may fail."
    )

ENDPOINT = f"{GRAPHDB_DOMAIN}/repositories/philharmonie-chatbot?query="
VOICE_CHANNELS = ["google_assistant", "alexa"]


class NoResultsException(Exception):
    pass


class NoEntityFoundException(Exception):
    pass


class ActionDirectQuery(Action):
    def __init__(self):
        super(ActionDirectQuery, self).__init__()

    def name(self) -> Text:
        return "action_direct_query"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ):
        # Get slots
        existing_slots = get_slots(tracker)
        logging.info(f"Existing_slots: {existing_slots}")

        slots_to_clear = self.clear_slots(existing_slots)
        logging.info(f"Slots_to_clear: {slots_to_clear}")

        # Display message
        msg = "Dites moi ce que vous cherchez, et je vais essayer de trouver des partitions qui y correspondent."
        dispatcher.utter_message(text=msg)

        return slots_to_clear

    def clear_slots(self, existing_slots):
        # We clear every slot which is not in the entities
        slots = []
        for slot_name in existing_slots:
            slots.append(SlotSet(slot_name, None))

        return slots


class ActionDisplayResults(Action):
    def __init__(self):
        super(ActionDisplayResults, self).__init__()

    def name(self) -> Text:
        return "action_display_results"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ):
        current_results = tracker.get_slot("current_results")
        current_results = urllib.parse.unquote_plus(current_results)
        logging.info(f"current_results: {current_results}")

        entities = sorted(tracker.latest_message["entities"], key=lambda d: d["start"])
        logging.info(entities)

        # Criterias button
        buttons = ActionGetSheetMusicByCasting.get_criteria_buttons(tracker, None)
        # Start new search button
        buttons.append(
            {
                "title": "Nouvelle recherche",
                "payload": "/direct_query",
            }
        )

        # Display message
        dispatcher.utter_message(text=current_results, buttons=buttons)
        return []


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


select distinct ?score ?scoreResearch ?snippetField ?snippetText ?identifier ?scoreUrl  ?scoreTitleLabel ?genrelabel ?localisationLabel ?periodLabel ?responsibilityLabel ?educationLevelLabel ?agent ?agentLabel ?roleLabel ?input_quantity_total ?compositeurLabel

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .
    {filters}

# les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
# on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
order by desc (?scoreResearch)
        """
        self.allowed_medias = list(medias.iaml.keys()) + list(medias.mimo.keys())

    def name(self) -> Text:
        return "action_get_sheet_music_by_casting"

    def set_entities(
        self,
        entities,
    ):
        inputted_medias = dict()
        entity_dict = defaultdict(lambda: defaultdict(lambda: None))

        for i, ent in enumerate(entities):
            if ent["entity"] == "medium":
                medium = ent.get("value")
                if medium.isdigit() and medium not in self.allowed_medias:
                    entity_dict = self.reassign_type(medium, entity_dict)
                else:
                    if medium not in self.allowed_medias:
                        medium, medium_name = self.get_closest_event(
                            medium, {**medias.iaml, **medias.mimo}
                        )
                        if medium is None:
                            continue
                    # Check if the medium has been entered after a number or formation
                    if i > 0 and entities[i - 1]["entity"] in [
                        "number",
                        "formation",
                    ]:
                        entity = entities[i - 1]["entity"]
                        volume = entities[i - 1]["value"]
                        if entity == "formation" and not volume.isdigit():
                            volume, _ = self.get_closest_event(
                                volume, formations.formations
                            )
                        if volume is None:
                            raise NoEntityFoundException(
                                f"Number/Formation entity with no value: {entities}"
                            )
                        inputted_medias[medium] = int(volume)
                    else:
                        inputted_medias[medium] = 1

            if ent["entity"] == "level" and entity_dict["level"]["code"] is None:
                level = ent.get("value")
                if level not in levels.all_levels:
                    level, level_name = self.get_closest_event(level, levels.all_levels)
                    logging.info(f"Parsed level: {level}")
                if level is None:
                    raise NoEntityFoundException(
                        f"Level entity with no value: {entities}"
                    )
                entity_dict["level"] = {  # type: ignore
                    "code": level,
                    "name": levels.all_levels.get(level, [None])[0],
                }

            if (
                ent["entity"] == "formation"
                and entity_dict["formation"]["code"] is None
            ):
                formation = ent.get("value")
                if formation not in formations.formations:
                    formation, formation_name = self.get_closest_event(
                        formation, formations.formations
                    )
                    logging.info(f"Parsed formation: {formation}")
                # Is the formation the total number of instruments OR a specific medium count?
                j = i
                while j < len(entities) - 1:
                    # If there is a number between formation and the next medium, then formation is the total
                    if entities[j]["entity"] == "number":
                        break
                    # Else if there's a medium directly after, then formation is just this medium's count
                    elif entities[j]["entity"] == "medium":
                        formation = None
                        break
                    j += 1
                if formation is None:
                    raise NoEntityFoundException(
                        f"Formation entity with no value: {entities}"
                    )
                entity_dict["formation"] = {  # type: ignore
                    "code": formation,
                    "name": formations.formations.get(formation, [None, None])[1],
                }

            if ent["entity"] == "genre" and entity_dict["genre"]["code"] is None:
                genre = ent.get("value")
                if genre.isdigit() and genre not in genres.genres:
                    entity_dict = self.reassign_type(genre, entity_dict)
                else:
                    if genre not in genres.genres:
                        genre, _ = self.get_closest_event(genre, genres.genres)
                        logging.info(f"Parsed genre: {genre}")
                    if genre is None:
                        raise NoEntityFoundException(
                            f"Genre entity with no value: {entities}"
                        )
                    entity_dict["genre"] = {  # type: ignore
                        "code": genre,
                        "name": genres.genres.get(genre, [None])[0],
                    }

            if ent["entity"] == "agent" and entity_dict["agent"]["code"] is None:
                agent = ent.get("value")
                if agent.isdigit() and agent not in agents.agents:
                    entity_dict = self.reassign_type(agent, entity_dict)
                else:
                    if agent not in agents.agents:
                        agent, _ = self.get_closest_event(agent, agents.agents)
                        logging.info(f"Parsed agent: {agent}")
                    if agent is None:
                        raise NoEntityFoundException(
                            f"Agent entity with no value: {entities}"
                        )
                    entity_dict["agent"] = {  # type: ignore
                        "code": agent,
                        "name": agents.agents.get(agent, [None])[0],
                    }

            if ent["entity"] == "period" and entity_dict["period"]["code"] is None:
                period = ent.get("value")
                if period.isdigit() and period not in periods.periods:
                    entity_dict = self.reassign_type(period, entity_dict)
                else:
                    if period not in periods.periods:
                        period, _ = self.get_closest_event(period, periods.periods)
                        logging.info(f"Parsed period: {period}")
                    if period is None:
                        raise NoEntityFoundException(
                            f"Period entity with no value: {entities}"
                        )
                    entity_dict["period"] = {  # type: ignore
                        "code": period,
                        "name": periods.periods.get(period, [None])[0],
                    }

            if ent["entity"] == "location" and entity_dict["location"]["code"] is None:
                location = ent.get("value")
                if location.isdigit() and location not in locations.locations:
                    entity_dict = self.reassign_type(location, entity_dict)
                else:
                    if location not in locations.locations:
                        location, _ = self.get_closest_event(
                            location, locations.locations
                        )
                        logging.info(f"Parsed location: {location}")
                    if location is None:
                        raise NoEntityFoundException(
                            f"Location entity with no value: {entities}"
                        )
                    entity_dict["location"] = {  # type: ignore
                        "code": location,
                        "name": locations.locations.get(location, [None])[0],
                    }

            if (
                ent["entity"] == "work_name"
                and entity_dict["work_name"]["code"] is None
            ):
                work_name = ent.get("value")
                if work_name.isdigit():
                    entity_dict = self.reassign_type(work_name, entity_dict)
                else:
                    entity_dict["work_name"] = {  # type: ignore
                        "code": work_name,
                        "name": work_name,
                    }

        return inputted_medias, entity_dict

    def get_name_from_code(self, slot_name, code):
        """Get the name from the code."""
        if slot_name == "genre":
            return genres.genres.get(code, [None])[0]
        elif slot_name == "agent":
            return agents.agents.get(code, [None])[0]
        elif slot_name == "period":
            return periods.periods.get(code, [None])[0]
        elif slot_name == "location":
            return locations.locations.get(code, [None])[0]
        elif slot_name == "level":
            return levels.all_levels.get(code, [None])[0]
        elif slot_name == "work_name":
            return code
        else:
            raise ValueError(f"Unknown slot name: {slot_name}")

    def clear_slots(self, existing_slots, entity_dict, inputted_medias):
        # We clear every slot which is not in the entities
        slots = []
        to_pop = []
        for slot_name, slot_value in existing_slots.items():
            # Instrumentation
            if slot_name == "instrumentation" and inputted_medias:
                slots.append(SlotSet("instrumentation", str(inputted_medias)))
                to_pop.append("instrumentation")
            # Rest of the slots
            elif slot_name not in entity_dict and slot_value is not None:
                slots.append(SlotSet(slot_name, None))
                to_pop.append(slot_name)
            else:
                slots.append(SlotSet(slot_name, entity_dict[slot_name]["code"]))

        # This below is necessary because we can't pop while iterating
        for slot_name in to_pop:
            existing_slots.pop(slot_name)

        return slots, existing_slots

    def slots_to_entities(self, slots, entity_dict, inputted_medias):
        """Patch the entity_dict with the slots."""
        for slot_name, slot_value in slots.items():
            if entity_dict[slot_name]["code"] is not None or slot_value is None:
                continue
            if slot_name != "instrumentation":
                entity_dict[slot_name]["code"] = slot_value
                entity_dict[slot_name]["name"] = self.get_name_from_code(
                    slot_name, slot_value
                )
            if slot_name == "instrumentation":
                instru_dict = ast.literal_eval(slot_value)
                for media_code, media_count in instru_dict.items():
                    if media_code not in inputted_medias:
                        inputted_medias[media_code] = media_count
        logging.info(
            f"PATCHED ENTITY dict: {entity_dict};\n inputted_medias: {inputted_medias}"
        )

        return entity_dict, inputted_medias

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Get entities
        entities = sorted(tracker.latest_message["entities"], key=lambda d: d["start"])
        logging.info(entities)

        existing_slots = get_slots(tracker)
        logging.info(f"Existing_slots: {existing_slots}")

        # Initialize output variables
        worded_mediums = ""
        results = []
        buttons = []
        slots = []
        try:
            # Set entities
            inputted_medias, entity_dict = self.set_entities(
                entities,
            )

            # If inputted_medias is None, empty, or contains no key of medias.medias, throw error
            if inputted_medias and not set(inputted_medias.keys()).issubset(
                self.allowed_medias
            ):
                raise NoEntityFoundException(
                    f"Problem with entities: {inputted_medias}"
                )

            # Check if previous intent is get_sheet_music_by_casting. If yes, then clear slots
            if (
                tracker.latest_message["intent"].get("name")
                == "get_sheet_music_by_casting"
            ):
                logging.info("Clearing slots")
                slots_to_clear, existing_slots = self.clear_slots(
                    existing_slots, entity_dict, inputted_medias
                )
                slots.extend(slots_to_clear)
            else:
                if inputted_medias:
                    slots.append(SlotSet("instrumentation", str(inputted_medias)))
                logging.info(f"medium: {inputted_medias}, entity_dict: {entity_dict}")
                entity_dict, inputted_medias = self.slots_to_entities(
                    existing_slots, entity_dict, inputted_medias
                )

            results, worded_mediums, ids = self.get_query_results(
                inputted_medias, entity_dict, exclusive=True
            )

            # Add the user-inputted criterias to the answer
            answer = self.add_criterias(entity_dict, worded_mediums)

            if not results:
                results, worded_mediums, ids = self.get_query_results(
                    inputted_medias, entity_dict
                )
                if results:
                    answer += "Je n'ai pas trouvé de résultats comportant uniquement l'instrumentation que vous avez spécifié, j'ai donc élargi la recherche aux partitions comportant également d'autres instruments.\n"
                else:
                    raise NoResultsException(
                        f"No results found for medias: {inputted_medias}"
                    )

            # User wants to see the results (action called natively, from outside the "button flow")
            new_answer, buttons = self.format_answer_without_results(
                entity_dict,
                results,
                inputted_medias,
                ids,
            )

            answer += new_answer
        except Exception:
            logging.info(traceback.print_exc())
            answer = "Vous recherchez des partitions, mais je n'ai pas trouvé de résultats correspondant à votre recherche. Veuillez reformuler votre demande."
            # answer += self.add_criterias(entity_dict, worded_mediums)
        dispatcher.utter_message(text=answer, buttons=buttons)
        return slots

    def get_query_results(
        self, inputted_medias: dict, entity_dict: dict, exclusive=False
    ) -> Tuple[List[dict], str, List[str]]:
        formatted_query, worded_mediums = self.format_sparql_query(
            inputted_medias, entity_dict, exclusive
        )
        route = ENDPOINT + formatted_query
        results = requests.get(
            route,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN,
            },
        ).json()
        texts = []
        ids = []
        for res in results["results"]["bindings"]:
            try:
                ids.append(res["score"]["value"].split("/")[-1])
            except:
                logging.info(f"No score found, could not add {res} to results")
            url = res["scoreUrl"]["value"]
            title = res["scoreTitleLabel"]["value"]
            compositeur = res.get("compositeurLabel", {"value": ""})["value"]
            if DEBUG and entity_dict["work_name"]["code"] is not None:
                score = res.get("scoreResearch", {}).get("value", "")
                try:
                    score = str(round(float(score), 2))
                except:
                    score = ""
                texts.append(f"- {f'[{score}]'} [{title}]({url}), {compositeur}")
            else:
                texts.append(f"- [{title}]({url}), {compositeur}")
        return texts, worded_mediums, ids

    def format_sparql_query(
        self, inputted_medias: dict, entity_dict: dict, exclusive: bool
    ) -> str:
        filters = ""
        solo_medium_filters = ""
        worded_mediums = ""
        medium_sums = []

        for i, medium in enumerate(inputted_medias.keys()):
            # Check if mimo or iaml

            if medium.isdigit():
                formatted_medium = (
                    f"<http://www.mimo-db.eu/InstrumentsKeywords/{medium}>"
                )
                worded_mediums += f"{inputted_medias[medium]} {medias.mimo[medium][0]}"
            else:
                formatted_medium = (
                    f"<http://data.doremus.org/vocabulary/iaml/mop/{medium}>"
                )
                worded_mediums += f"{inputted_medias[medium]} {medias.iaml[medium][0]}"

            if exclusive and i == len(inputted_medias) - 2:
                worded_mediums += " et "
            elif not exclusive and i == len(inputted_medias) - 1:
                worded_mediums += " et d'autres instruments"
            elif i < len(inputted_medias) - 1:
                worded_mediums += ", "

            count = inputted_medias[medium]
            medium_sums.append(f"SUM(?mediumQuantity_{i}) >= {count}")

            # Medium
            solo_medium_filters += f"""
#selection instrument {i}          
?casting mus:U23_has_casting_detail ?castingDetail_{i}.
?castingDetail_{i}
    philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal {formatted_medium} ;
    mus:U30_foresees_quantity_of_mop ?mediumQuantity_{i}. 
            """

        if inputted_medias:
            filters += f"""
# FILTRAGE SUR L'INSTRUMENTATION    
{{
    SELECT ?score ?casting 
    WHERE {{
        ?score a ?classes.
        values (?classes ) {{ (efrbroo:F24_Publication_Expression)(mus:M167_Publication_Expression_Fragment)}}
        ?score mus:U13_has_casting ?casting .
        {solo_medium_filters}
    }}
    GROUP BY ?score ?casting
    # filtre sur les quantités d'instruments (à supprimer si pas de contrainte sur les quantités de chaque instrument)        
    HAVING({' && '.join(medium_sums)})
}}
            """

        # calculer la quantité totale d'instruments
        if exclusive and inputted_medias:
            if entity_dict["formation"]["code"] is not None:
                total = entity_dict["formation"]["code"]
            else:
                total = sum(inputted_medias.values())
            logging.info(f"Using strict instrument total: {total}")
            filters += f"""
values (?input_quantity_total) {{(\"{total}\"^^xsd:integer)}}
?casting mus:U48_foresees_quantity_of_actors ?input_quantity_total.
            """

        # Level
        if entity_dict["level"]["code"] is not None:
            filters += f"""
values (?input_educational_level) {{ (<https://data.philharmoniedeparis.fr/vocabulary/edudational-level/{entity_dict["level"]["code"]}>)}}
?casting mus:U23_has_casting_detail ?castingDetailNiveauEducatif.
?castingDetailNiveauEducatif ecrm:P103_was_intended_for ?input_educational_level.
?input_educational_level skos:prefLabel ?educationLevelLabel.
graph <http://data.philharmoniedeparis.fr/graph/scores> 
{{ ?castingDetailNiveauEducatif
    philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?mediumNiveauEducatif.}}
?mediumNiveauEducatif skos:prefLabel ?mediumNiveauEducatifLabel.
filter (lang(?mediumNiveauEducatifLabel)="fr")
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
values (?input_agent ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{entity_dict["agent"]["code"]}>) }}
values (?input_agent_role ) {{ (<https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/230>) (<https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/040> )(<https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/590> )}}
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
?score mus:U66_has_historical_context ?input_period.
?input_period skos:prefLabel ?periodLabel.
"""

        if entity_dict["work_name"]["code"] is not None:
            lucene_query = " AND ".join(
                [word + "~0.6" for word in entity_dict["work_name"]["code"].split(" ")]
            )
            logging.info(lucene_query)
            filters += f"""
{{
    SELECT ?score ?casting ?snippetText ?snippetField ?scoreResearch 
    WHERE {{
    ?search a luc-index:TitleIndex ;
        luc:query "{lucene_query}" ;  
        luc:entities ?score .
        ?score luc:score ?scoreResearch .
        ?score luc:snippets ?snippet .
        ?snippet luc:snippetField ?snippetField ;
        luc:snippetText ?snippetText .
    }}
}}
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
optional {{?creation  mus:R24_created   ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by ?compositeur.
?task mus:U31_had_function <https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/230>.
?compositeur rdfs:label ?compositeurLabel.}}
"""

        query = self.route.format(filters=filters)
        logging.info(f"Requesting {query}")

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        return parsed_query, worded_mediums

    def get_closest_event(self, value: str, candidates: Dict = None):
        # Use fuzz ratio to compare value to the candidates in the dictionary
        # Return highest match
        closest_match = None
        closest_match_ratio = 85
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
            "location": locations.locations,
            "medium": {**medias.iaml, **medias.mimo},
        }
        for entity_type, authorized in authorized_values.items():
            if entity_code in authorized:
                entity_dict[entity_type]["code"] = entity_code
                entity_dict[entity_type]["name"] = authorized[entity_code][0]
                return entity_dict
        return entity_dict

    @staticmethod
    def add_criterias(entity_dict, worded_mediums):
        """
        Create a string with all the criterias that were inputted by the user
        """
        # Add to criterias, all the entities that have a name
        criterias = [
            val["name"] for val in entity_dict.values() if val["name"] is not None
        ]

        res = "Vous recherchez des partitions"

        # Add the worded mediums, i.e. the instruments in human-readable form
        if worded_mediums:
            criterias += [worded_mediums]

        if criterias:
            # Format the string differently depending on the number of criterias
            res += (
                f" avec les critères " if len(criterias) > 1 else f" avec le critère "
            )
            for i, entity_name in enumerate(criterias):
                res += f" {entity_name}"
                if i < len(criterias) - 2:
                    res += ","
                elif i == len(criterias) - 2:
                    res += " et"
        res += ". "
        return res

    @staticmethod
    def format_answer_with_results(
        results,
    ):
        # Format the results
        formatted_results = "\n".join(results)

        # Format the bot answer
        buttons = []
        worded_results = f"Voici les "
        if len(results) >= MAX_RESULTS_TOTAL:
            worded_results += f"{MAX_RESULTS_TOTAL} premières "
        worded_results += "partitions que j'ai trouvées"
        worded_results += f":\n{formatted_results}"

        events = []

        return worded_results, buttons, events

    @staticmethod
    def format_results_url(ids):
        base_url = "https://catalogue.philharmoniedeparis.fr/search.aspx?SC=CATALOGUE&QUERY=Identifier_idx%3A({})+#/Search/(query:(InitialSearch:!t,Page:0,PageRange:3,QueryString:'Identifier_idx:({})%20',ResultSize:-1,ScenarioCode:CATALOGUE,SearchContext:0,SearchLabel:'Recherche%20depuis%20le%20chatbot'))"

        id_string = " OR ".join(ids)
        id_string_encoded = urllib.parse.quote(id_string)

        return base_url.format(id_string_encoded, id_string_encoded)

    @staticmethod
    def format_answer_without_results(entity_dict, results, inputted_medias, ids):
        # Format the bot answer
        buttons = []
        worded_results = f"J'ai trouvé {len(results)} partitions correspondant à votre recherche. Faites votre choix.\n"

        # String of results, passed as entity to the next action
        formatted_results = "\n".join(results[:MAX_RESULTS_TOTAL])

        # Add the url containing the ids to the results
        ids_count = min(100, len(ids))
        if ids_count > MAX_RESULTS_TOTAL:
            results_wording = f"la liste des {ids_count} premiers résultats"
        elif ids_count > 1:
            results_wording = f"les {ids_count} résultats"
        else:
            results_wording = f"le résultat"
        formatted_results += f"\n\nVous pouvez aussi consulter [{results_wording} sur le catalogue de la Philharmonie]({ActionGetSheetMusicByCasting.format_results_url(ids[:ids_count])})."

        logging.info(f"formatted_results: {formatted_results}")

        # Encode the full results
        encoded = urllib.parse.quote_plus(formatted_results.strip("\n"), safe="/")

        buttons.append(
            {
                "title": "Afficher les 25 premiers résultats"
                if len(results) > 25
                else f"Afficher les résultats",
                "payload": f'/display_results{{"current_results": "{encoded}"}}',
            }
        )
        criteria_buttons = ActionGetSheetMusicByCasting.get_criteria_buttons(
            entity_dict, inputted_medias
        )
        buttons.extend(criteria_buttons)
        logging.info(f"buttons: {buttons}")

        return worded_results, buttons

    @staticmethod
    def get_criteria_buttons(source, inputted_medias):
        buttons = []

        if isinstance(source, dict):
            # In this case the source is a dict and we need to get the value like so:
            getter = lambda value_name: source[value_name]["code"]
            instrumentation = inputted_medias
        else:
            # In this case the source is a tracker and we need to get the value like so:
            getter = lambda value_name: source.get_slot(value_name)
            instrumentation = getter("instrumentation")

        agent = getter("agent")
        if not agent:
            buttons.append(
                {
                    "title": f"Compositeur",
                    "payload": f"/composer_choice",
                }
            )

        if not instrumentation:
            buttons.append(
                {
                    "title": f"Instrumentation",
                    "payload": f"/instrumentation_choice",
                }
            )

        genre = getter("genre")
        if not genre:
            buttons.append(
                {
                    "title": f"Genre",
                    "payload": f"/genre_choice",
                }
            )

        location = getter("location")
        if not location:
            buttons.append(
                {
                    "title": f"Localisation",
                    "payload": f"/location_choice",
                }
            )

        period = getter("period")
        if not period:
            buttons.append(
                {
                    "title": f"Période",
                    "payload": f"/period_choice",
                }
            )

        level = getter("level")
        if not level:
            buttons.append(
                {
                    "title": f"Niveau",
                    "payload": f"/level_choice",
                }
            )

        work_name = getter("work_name")
        if not work_name:
            buttons.append(
                {
                    "title": f"Nom de l'oeuvre",
                    "payload": f"/work_name_manual_entry",
                }
            )
        return buttons


def get_slots(tracker):
    return {
        "agent": tracker.get_slot("agent"),
        "instrumentation": tracker.get_slot("instrumentation"),
        "genre": tracker.get_slot("genre"),
        "location": tracker.get_slot("location"),
        "period": tracker.get_slot("period"),
        "level": tracker.get_slot("level"),
        "work_name": tracker.get_slot("work_name"),
    }


def get_choice_filters(tracker):
    slots = get_slots(tracker)
    logging.info(f"slots: {slots}")
    filters = ""
    if slots["agent"]:
        filters += ActionComposerChoice.get_agent_filter(slots["agent"])
    if slots["instrumentation"]:
        filters += ActionInstrumentationChoice.get_instrumentation_filter(
            slots["instrumentation"]
        )
    if slots["genre"]:
        filters += ActionGenreChoice.get_genre_filter(slots["genre"])
    if slots["location"]:
        filters += ActionLocationChoice.get_location_filter(slots["location"])
    if slots["period"]:
        filters += ActionPeriodChoice.get_period_filter(slots["period"])
    if slots["level"]:
        filters += ActionLevelChoice.get_level_filter(slots["level"])
    if slots["work_name"]:
        filters += ActionWorkNameChoice.get_work_name_filter(slots["work_name"])
    return filters


class ActionComposerChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?compositeur ?compositeurLabel (count(distinct ?score) as ?scoreCount)
where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .

    {filters}

    # AGENT
    optional {{?creation  mus:R24_created   ?score .
    ?creation ecrm:P9_consists_of ?task.
    ?task ecrm:P14_carried_out_by ?compositeur.
    ?task mus:U31_had_function <https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/230>.
    ?compositeur rdfs:label ?compositeurLabel.}}

    # les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
    # on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?compositeur ?compositeurLabel
ORDER BY DESC(?scoreCount)
        """

    def name(self):
        return "action_composer_choice"

    def run(self, dispatcher, tracker, domain):
        # Get the filters
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get composers
        try:
            composers = self.get_top_composers(filters)

            buttons = []
            for composer in composers:
                buttons.append(
                    {
                        "title": composer["compositeurLabel"]["value"],
                        "payload": f'/composer_is_selected{{"agent":"{composer["compositeur"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre compositeur",
                    "payload": "/composer_manual_entry",
                }
            )

            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques compositeurs principaux pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les compositeurs relatifs à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the composers slot
        return []

    def get_top_composers(self, filters: str):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if "compositeur" not in results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["compositeur"]["value"] = str(
                int(r["compositeur"]["value"].split("/")[-1])
            )
            res.append(r)
        return res

    @staticmethod
    def get_agent_filter(agent: str):
        while len(agent) < 7:
            agent = "0" + agent
        return f"""
?creation  mus:R24_created   ?score .
?creation ecrm:P9_consists_of ?task.
?task ecrm:P14_carried_out_by <https://ark.philharmoniedeparis.fr/ark:49250/{agent}>.
?task mus:U31_had_function <https://ark.philharmoniedeparis.fr/ark/49250/vocabulary/roles/230>.
"""


class ActionInstrumentationChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?medium ?mediumLabel (count(distinct ?score) as ?scoreCount)

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .

    {filters}

# les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
# on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?medium ?mediumLabel
ORDER BY DESC(?scoreCount)
        """

    def name(self):
        return "action_instrumentation_choice"

    def run(self, dispatcher, tracker, domain):
        # Get the current slot values
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get formations
        try:
            formations = self.get_top_instrumentations(filters)

            buttons = []
            for formation in formations:
                buttons.append(
                    {
                        "title": formation["mediumLabel"]["value"],
                        "payload": f'/instrumentation_is_selected{{"medium":"{formation["medium"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre instrumentation",
                    "payload": "/instrumentation_manual_entry",
                }
            )

            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques instrumentations principales pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les instrumentations relatives à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the formations slot
        return []

    def get_top_instrumentations(self, filters):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")

        # Launch the query
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if not results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["medium"]["value"] = r["medium"]["value"].split("/")[-1]
            res.append(r)
        return res

    @staticmethod
    def get_instrumentation_filter(instrumentation: str):
        filters = ""
        solo_medium_filters = ""
        medium_sums = []

        # Parse the str repr of the instrumentation dict to a dict using
        instru_dict = ast.literal_eval(instrumentation)
        if not instru_dict:
            return ""

        for i, medium in enumerate(instru_dict.keys()):
            # Check if mimo or iaml

            if medium.isdigit():
                formatted_medium = (
                    f"<http://www.mimo-db.eu/InstrumentsKeywords/{medium}>"
                )
            else:
                formatted_medium = (
                    f"<http://data.doremus.org/vocabulary/iaml/mop/{medium}>"
                )

            count = instru_dict[medium]
            medium_sums.append(f"SUM(?mediumQuantity_{i}) >= {count}")

            # Medium
            solo_medium_filters += f"""
#selection instrument {i}          
?casting mus:U23_has_casting_detail ?castingDetail_{i}.
?castingDetail_{i}
    philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal {formatted_medium} ;
    mus:U30_foresees_quantity_of_mop ?mediumQuantity_{i}. 
            """

        filters += f"""
# FILTRAGE SUR L'INSTRUMENTATION    
{{
SELECT ?score ?casting 
WHERE {{
    ?score a ?classes.
    values (?classes ) {{ (efrbroo:F24_Publication_Expression)(mus:M167_Publication_Expression_Fragment)}}
    ?score mus:U13_has_casting ?casting .
    {solo_medium_filters}
}}
GROUP BY ?score ?casting
# filtre sur les quantités d'instruments (à supprimer si pas de contrainte sur les quantités de chaque instrument)        
HAVING({' && '.join(medium_sums)})
}}
        """
        # DEPRECATED: The below filter selects exact quantities of instruments, will break
        # on chorals or ensembles which we don't care about anyway when finding the top
        # genres or composers etc. using the instrumentation
        #
        # total = sum(instru_dict.values())
        # filters += f"""
        # values (?input_quantity_total) {{(\"{total}\"^^xsd:integer)}}
        # ?casting mus:U48_foresees_quantity_of_actors ?input_quantity_total.
        # """
        return filters


class ActionGenreChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?genre ?genreLabel (count(distinct ?score) as ?scoreCount)

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .
        
    ?score mus:U12_has_genre ?genre.
    ?genre skos:prefLabel ?genreLabel.

    {filters}

    # les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
    # on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?genre ?genreLabel
ORDER BY DESC(?scoreCount)
"""

    def name(self):
        return "action_genre_choice"

    def run(self, dispatcher, tracker, domain):
        # Get filters
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get formations
        try:
            genres = self.get_top_genres(filters)

            buttons = []
            for genre in genres:
                buttons.append(
                    {
                        "title": genre["genreLabel"]["value"],
                        "payload": f'/genre_is_selected{{"genre":"{genre["genre"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre genre",
                    "payload": "/genre_manual_entry",
                }
            )

            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques genres principaux pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les genres relatifs à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the formations slot
        return []

    def get_top_genres(self, filters: str):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")

        # Launch the query
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if not results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["genre"]["value"] = str(int(r["genre"]["value"].split("/")[-1]))
            res.append(r)
        return res

    @staticmethod
    def get_genre_filter(genre: str):
        while len(genre) < 7:
            genre = "0" + genre
        return f"""
values (?genre ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{genre}>)}}
?score mus:U12_has_genre ?genre.
        """


class ActionLocationChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?localisation ?localisationLabel (count(distinct ?score) as ?scoreCount)

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .
        
    {filters}

?score mus:U65_has_geographical_context ?localisation.
?localisation skos:prefLabel ?localisationLabel.


# les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    

    # les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
    # on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?localisation ?localisationLabel
ORDER BY DESC(?scoreCount)
"""

    def name(self):
        return "action_location_choice"

    def run(self, dispatcher, tracker, domain):
        # Get filters
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get formations
        try:
            locations = self.get_top_locations(filters)

            buttons = []
            for location in locations:
                buttons.append(
                    {
                        "title": location["localisationLabel"]["value"],
                        "payload": f'/location_is_selected{{"location":"{location["localisation"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre lieu",
                    "payload": "/location_manual_entry",
                }
            )
            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques lieux principaux pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les lieux relatifs à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the formations slot
        return []

    def get_top_locations(self, filters: str):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")

        # Launch the query
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if not results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["localisation"]["value"] = str(
                int(r["localisation"]["value"].split("/")[-1])
            )
            res.append(r)
        return res

    @staticmethod
    def get_location_filter(location: str):
        while len(location) < 7:
            location = "0" + location
        return f"""
values (?localisation) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{location}>) }}
?score mus:U65_has_geographical_context ?localisation.
?localisation skos:prefLabel ?localisationLabel.
"""


class ActionPeriodChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?period ?periodLabel (count(distinct ?score) as ?scoreCount)

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .
        
    {filters}
    
?score mus:U66_has_historical_context ?period.
?period skos:prefLabel ?periodLabel.

    # les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
    # on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?period ?periodLabel
ORDER BY DESC(?scoreCount)
"""

    def name(self):
        return "action_period_choice"

    def run(self, dispatcher, tracker, domain):
        # Get filters
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get formations
        try:
            periods = self.get_top_periods(filters)

            buttons = []
            for period in periods:
                buttons.append(
                    {
                        "title": period["periodLabel"]["value"],
                        "payload": f'/period_is_selected{{"period":"{period["period"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre période",
                    "payload": "/period_manual_entry",
                }
            )

            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques périodes principales pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les périodes relatives à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the formations slot
        return []

    def get_top_periods(self, filters: str):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")

        # Launch the query
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if not results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["period"]["value"] = str(int(r["period"]["value"].split("/")[-1]))
            res.append(r)
        return res

    @staticmethod
    def get_period_filter(period: str):
        while len(period) < 7:
            period = "0" + period
        return f"""
values (?input_period ) {{ (<https://ark.philharmoniedeparis.fr/ark:49250/{period}>)}}
?score mus:U66_has_historical_context ?input_period.
?input_period skos:prefLabel ?periodLabel.
"""


class ActionLevelChoice(Action):
    def __init__(self):
        self.query = """
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


select distinct ?level ?levelLabel (count(distinct ?score) as ?scoreCount)

where {{
    ?score a <http://erlangen-crm.org/efrbroo/F24_Publication_Expression>.
    ?score mus:U13_has_casting ?casting .
    ?casting mus:U23_has_casting_detail ?castingDetail .

    {filters}
        
?casting mus:U23_has_casting_detail ?castingDetailNiveauEducatif.
?castingDetailNiveauEducatif ecrm:P103_was_intended_for ?level.
?level skos:prefLabel ?levelLabel.
graph <http://data.philharmoniedeparis.fr/graph/scores> 
{{ ?castingDetailNiveauEducatif
    philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?mediumNiveauEducatif.}}
?mediumNiveauEducatif skos:prefLabel ?mediumNiveauEducatifLabel.
filter (lang(?mediumNiveauEducatifLabel)="fr")

        
    # les partitions avec leur titre et statement of responsibility ...
    ?score  mus:U170_has_title_statement ?scoreTitle.
    ?scoreTitle rdfs:label ?scoreTitleLabel.
    optional {{?score mus:U172_has_statement_of_responsibility_relating_to_title ?U172_has_statement_of_responsibility_relating_to_title. 
    ?U172_has_statement_of_responsibility_relating_to_title rdfs:label ?responsibilityLabel}}
    
    # on veut récupérer tous les instruments du casting
    #on ne tient pas compte des instruments ajoutés lors de la surindexation
    graph <http://data.philharmoniedeparis.fr/graph/scores> 
    {{
    ?castingDetail philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?medium.
    }}
	optional {{?medium skos:prefLabel ?mediumLabel.
	filter (lang(?mediumLabel)="fr")}}
    optional {{ ?castingDetail mus:U30_foresees_quantity_of_mop ?mediumQuantity.}}

# construction de l'URL dans le site de la philharmonie
    bind (strafter(str(?score),"ark:49250/")as ?identifier)
    BIND(CONCAT("https://catalogue.philharmoniedeparis.fr/doc/ALOES/", SUBSTR(?identifier, 1,8)) AS ?scoreUrl)
}}
GROUP BY ?level ?levelLabel
ORDER BY DESC(?scoreCount)
"""

    def name(self):
        return "action_level_choice"

    def run(self, dispatcher, tracker, domain):
        # Get filters
        filters = get_choice_filters(tracker)
        logging.debug(f"Filters: {filters}")

        # Query the graph DB to get formations
        try:
            levels = self.get_top_levels(filters)

            buttons = []
            for level in levels:
                buttons.append(
                    {
                        "title": level["levelLabel"]["value"],
                        "payload": f'/level_is_selected{{"level":"{level["level"]["value"]}"}}',
                    }
                )

            # Append manual entry button
            buttons.append(
                {
                    "title": "Autre niveau",
                    "payload": "/level_manual_entry",
                }
            )

            # Display the buttons
            dispatcher.utter_message(
                text="Voilà quelques niveaux principaux pour filtrer les résultats:",
                buttons=buttons,
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            dispatcher.utter_message(
                text="Désolé, je n'ai pas réussi à récupérer les niveaux relatifs à votre recherche. Essayez un autre critère, ou inspectez directement les résultats.",
                buttons=ActionGetSheetMusicByCasting.get_criteria_buttons(
                    tracker, None
                ),
            )

        # Set the formations slot
        return []

    def get_top_levels(self, filters: str):
        # Format the query string
        query = self.query.format(filters=filters)

        parsed_query = urllib.parse.quote_plus(query, safe="/")
        logging.info(f"Requesting {query}")

        # Launch the query
        results = requests.get(
            ENDPOINT + parsed_query,
            headers={
                "Accept": "application/sparql-results+json",
                "Authorization": TOKEN if TOKEN else "",
            },
        ).json()
        res = []

        # pop any empty first element
        if not results["results"]["bindings"][0]:
            results["results"]["bindings"].pop(0)

        results_nb = min(len(results["results"]["bindings"]), 3)

        for r in results["results"]["bindings"][:results_nb]:
            r["level"]["value"] = r["level"]["value"].split("/")[-1]
            res.append(r)
        return res

    @staticmethod
    def get_level_filter(level: str):
        return f"""
values (?input_educational_level) {{ (<https://data.philharmoniedeparis.fr/vocabulary/edudational-level/{level}>)}}
?casting mus:U23_has_casting_detail ?castingDetailNiveauEducatif.
?castingDetailNiveauEducatif ecrm:P103_was_intended_for ?input_educational_level.
?input_educational_level skos:prefLabel ?educationLevelLabel.
graph <http://data.philharmoniedeparis.fr/graph/scores> 
{{ ?castingDetailNiveauEducatif
    philhar:S1_foresees_use_of_medium_of_performance_instrument | philhar:S2_foresees_use_of_medium_of_performance_vocal ?mediumNiveauEducatif.}}
?mediumNiveauEducatif skos:prefLabel ?mediumNiveauEducatifLabel.
filter (lang(?mediumNiveauEducatifLabel)="fr")
            """


class ActionWorkNameChoice(Action):
    def __init__(self):
        pass

    def name(self):
        return "action_work_name_choice"

    def run(self, dispatcher, tracker, domain):
        # Display the buttons
        dispatcher.utter_message(text="Tappez le nom de l'oeuvre que vous recherchez")
        # Set the formations slot
        return []

    @staticmethod
    def get_work_name_filter(work_name: str):
        lucene_query = " AND ".join([word + "~0.6" for word in work_name.split(" ")])
        logging.info(lucene_query)
        return f"""
{{
SELECT ?score ?casting ?snippetText ?snippetField ?scoreResearch 
WHERE {{
?search a luc-index:TitleIndex ;
    luc:query "{lucene_query}" ;  
    luc:entities ?score .
    ?score luc:score ?scoreResearch .
    ?score luc:snippets ?snippet .
    ?snippet luc:snippetField ?snippetField ;
    luc:snippetText ?snippetText .
}}
}}
"""
