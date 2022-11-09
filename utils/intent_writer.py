import itertools
import numpy as np

from medias_synonyms import iaml, mimo
from levels_synonyms import level_sentences, level_timing, level_worded
from genres_synonyms import genres
from agents_synonyms import agents
from formations_synonyms import formations
from periods_synonyms import periods
from locations_synonyms import locations
from write_entities import preprocess_entity


GENRES = np.repeat([preprocess_entity(i) for sublist in list(genres.values()) for i in sublist], 3)
AGENTS = np.random.choice([preprocess_entity(i) for sublist in list(agents.values()) for i in sublist], size=len(GENRES), replace=False)

raw_sentences = {
    "get_sheet_music_by_casting": {
        "sentences": [
            # MEDIUM
            "Quelles partitions avez-vous pour trois _MEDIUM et un _MEDIUM ?",
            "Je suis _MEDIUM et je cherche des partitions pour _MEDIUM et d'autres _MEDIUM.",
            "Pour un _MEDIUM, un _MEDIUM, et quatre _MEDIUM, quelles partitions?",
            "Je recherche une partition pour _MEDIUM et _MEDIUM ",
            "Avez-vous un morceau simple à me conseiller pour _MEDIUM et _MEDIUM ? ",
            "Je cherche des partitions de grands classiques, en version simplifiée, à jouer au _MEDIUM.",
            "Pourrais-je voir la liste de toutes vos partitions pour _MEDIUM ?",
            "_GENRE pour _MEDIUM",
            "Je voudrais trouver des arrangements de _GENRE pour _MEDIUM",
            "Je voudrais des jigs pour _MEDIUM ",
            "_MEDIUM tab",
            "Je cherche des partitions pour ensemble avec une _MEDIUM. Est-ce que ça existe?",
            "Nous sommes 4 musiciens (_MEDIUM, _MEDIUM, _MEDIUM, et _MEDIUM). Vous auriez des partitions que l’on pourrait jouer",
            "Est-ce que vous avez des répertoires de _GENRE pour _MEDIUM ?",
            "œuvres pour _MEDIUM",
            "Avez-vous des œuvres pour _MEDIUM ?",
            "_MEDIUM et _MEDIUM ?",

            # LEVELS
            "Je cherche quelque chose à jouer pour 2 _MEDIUM et une _MEDIUM avec un niveau _LEVEL_WORDED",
            "Je cherche des partitions pour musiciens avec un niveau _LEVEL_WORDED jouant du _MEDIUM et du _MEDIUM.",
            "Donnez moi les partitions avec un _MEDIUM et une _MEDIUM _LEVEL_SENTENCE.",
            "Liste partitions deux _MEDIUM pour musicien avec niveau _LEVEL_WORDED",
            "Quels sont les morceaux jouables par un groupe de 2 _MEDIUM ayant un niveau _LEVEL_WORDED?",
            "Je cherche des partitions pour musiciens jouant du _MEDIUM et du _MEDIUM depuis _LEVEL_TIMING.",
            "Je suis _MEDIUM et je cherche des partitions pour _MEDIUM pour élèves pratiquant depuis _LEVEL_TIMING. ",
            "Je cherche des _FORMATION avec une _MEDIUM _LEVEL_SENTENCE.",
            "Avez-vous une idée de morceau pour _MEDIUM et _MEDIUM  _LEVEL_SENTENCE? ",
            "Avez-vous des _FORMATION à jouer au _MEDIUM et au _MEDIUM _LEVEL_SENTENCE ?  ",
            "Un morceau pour un _FORMATION de _MEDIUM ayant _LEVEL_TIMING d'expérience",
            "Je recherche des _FORMATION pour _MEDIUM de niveau _LEVEL_WORDED",
            "Je recherche des _FORMATION _MEDIUM _MEDIUM _LEVEL_SENTENCE.",
            "Partition graphique pour _MEDIUM pour niveau _LEVEL_WORDED",
            "Je voudrais trouver des partitions pour 3 _MEDIUM, 2 _MEDIUM, 1 _MEDIUM et une _MEDIUM _LEVEL_SENTENCE",
            "Je cherche des partitions pour _MEDIUM pour des musiciens avec un niveau _LEVEL_WORDED",
            "Je souhaite trouver des œuvres pour _MEDIUM _LEVEL_SENTENCE",

            # GENRES
            "Je recherche une oeuvre _GENRE que l’on pourrait jouer avec un _MEDIUM, une _MEDIUM et un _MEDIUM",
            "Je veux une oeuvre _GENRE jouable par un _MEDIUM",
            "Donne moi des oeuvres _GENRE écrites pour _MEDIUM!",
            "Quelle oeuvre _GENRE pour _MEDIUM?",
            "Je cherche oeuvre _GENRE destinée à un _MEDIUM?",
            "Quelles sont les oeuvres _GENRE jouables par une _MEDIUM, une _MEDIUM et un _MEDIUM",
            "[Sonate]{\"entity\": \"genre\"} pour _MEDIUM",
            "je suis cheffe d'un ensemble vocal de 12 _MEDIUM et je cherche des transcriptions pour chœur de répertoire _GENRE.",
            "Je dirige un _MEDIUM et je cherche des partitions de _GENRE.",
            "Est-ce que vous auriez de la _GENRE, mais en notation occidentale ?",
            "Je recherche des partitions de _GENRE pour _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION à _MEDIUM",
            "Donne moi la liste des morceaux de _GENRE destinés à _FORMATION à _MEDIUM",
            "Je veux les partitions de _GENRE pour _FORMATION _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION de _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION _MEDIUM",
            "Je cherche des partitions de [musique contemporaine] {\"entity\": \"genre\"} pour _FORMATION [à cordes]{\"entity\": \"medium\"}",
            "Je recherche des partitions d'[opéra] {\"entity\": \"genre\"} pour [quatuors]{\"entity\": \"formation\"} [à corde]{\"entity\": \"medium\"}",
            "Je cherche des partitions de [jazz] {\"entity\": \"genre\"} pour _FORMATION [à vent]{\"entity\": \"medium\"}",
            "Je veux des partitions de [rock] {\"entity\": \"genre\"} écrites pour un _FORMATION [à corde]{\"entity\": \"medium\"}",
            "Je recherche des partitions de _GENRE",
            "Je voudrais des partitions de _GENRE",
            "J’aimerais accéder à un recueil de partitions de _GENRE de la fin du XVIème.",
            "Des fac- similés de partitions de _GENRE",
            "Vous avez des partitions de _GENRE ?",
            "Qu'est-ce qui existe pour _MEDIUM en _GENRE ?",
            "Je souhaite accéder à des partitions pour _MEDIUM composées en France entre 1792 et 1830",
            "Des partitions de _GENRE",
            "Des partitions de _GENRE pour _MEDIUM",
            "Des partitions pour _MEDIUM de _GENRE",
            "Des partitions de _GENRE pour _MEDIUM",
            "Des partitions pour _MEDIUM du _GENRE",
            "Je cherche des _MEDIUM du 19e siècle",
            "Je recherche des pièces pour _MEDIUM seule en _GENRE",
            "Nous sommes deux _MEDIUM et nous cherchons un _GENRE à jouer.",
            "je cherche des partitions de _GENRE pour _FORMATION à corde 2 _MEDIUM et _MEDIUM",
            "Je cherche des partitions de _GENRE pour _MEDIUM et _MEDIUM",
            "Je cherche des _GENRE",
            "Je cherche des scores pour groupe de _GENRE",
            "Je cherche des standards de _GENRE",
            "Je cherche des thèmes _GENRE",
            "Je cherche des chorus _GENRE",
            "Partitions de _GENRE",
            "Je recherche des arrangements/transcriptions de _GENRE (en tout genre)",
            "je cherche des _GENRE",

            # AGENTS
            "Donne moi les partitions pour une _MEDIUM et un _MEDIUM de _AGENT _LEVEL_SENTENCE.",
            "Je cherche la partition d'une oeuvre _GENRE de _AGENT",
            "Je cherche la partition d'une oeuvre de _AGENT _LEVEL_SENTENCE",
            "Est-ce que vous avez les sonates de _AGENT d’après-guerre ?",
            "Une collection intégrale des oeuvres d'_AGENT",
            "Une partition de _MEDIUM de la 5e Symphonie de _AGENT",
            "Les transcriptions de solos de _AGENT",
            "Avez-vous des partitions d'_AGENT de niveau _LEVEL_WORDED pour _MEDIUM et _MEDIUM ? ",
            "Avez-vous des partitions _MEDIUM écrites par _AGENT ?",
            "Avez-vous des partitions _MEDIUM écrites par _AGENT _LEVEL_SENTENCE?",
            "Je cherche les parties de _MEDIUM  pratiquant depuis _LEVEL_TIMING de _AGENT",
            "Où sont rangées les partitions pour _MEDIUM de _AGENT de niveau _LEVEL_WORDED ?",
            "Est-ce que _AGENT a composé des _FORMATION pour _MEDIUM et _MEDIUM ?",
            "J'aimerais savoir si vous avez des recueils de _GENRE dans lesquels je pourrais trouver du _AGENT ?",
            "Je cherche une _GENRE pour _MEDIUM et _MEDIUM de niveau _LEVEL_WORDE de _AGENT.",
            "Je cherche une _GENRE pour _MEDIUM et _MEDIUM de _AGENT.",
            "Je cherche une pièce de _AGENT pour _MEDIUM  et _MEDIUM _LEVEL_SENTENCE",
            "Je cherche une pièce de _AGENT pour _MEDIUM et _MEDIUM  pratiquant depuis _LEVEL_TIMING ",
            "Un songbook des _AGENT pour _MEDIUM et _MEDIUM _LEVEL_SENTENCE",
            "Les partitions pour _MEDIUM sur des poèmes de _AGENT",
            "Vous avez des partitions du _AGENT _LEVEL_SENTENCE?",
            "Vous avez des partitions de l'_AGENT ?",
            "Vous avez des partitions d'_AGENT _LEVEL_SENTENCE?",
            "Vous avez des partitions de _AGENT ?",

            "Quelles partitions de _AGENT avez-vous pour trois _MEDIUM et un _MEDIUM ?",
            "Pour un _MEDIUM, un _MEDIUM, et quatre _MEDIUM, quelles partitions de _AGENT?",
            "Je recherche une partition d'_AGENT pour _MEDIUM et _MEDIUM  eleves depuis _LEVEL_TIMING",
            "Avez-vous un morceau simple de _AGENT à me conseiller pour _MEDIUM et _MEDIUM ? ",
            "Je recherche une oeuvre _GENRE composee par _AGENT que l'on pourrait jouer avec un _MEDIUM, une _MEDIUM et un _MEDIUM",
            "Je cherche des partitions de grands classiques de _AGENT, en version simplifiée, à jouer au _MEDIUM.",
            "Pourrais-je voir la liste de toutes vos partitions _AGENT pour _MEDIUM ?",
            "Je voudrais trouver des arrangements de _GENRE de _AGENT pour _MEDIUM",
            "Je voudrais des jigs pour _MEDIUM crees par _AGENT",
            "_MEDIUM tab",
            "Je cherche les partitions du _AGENT pour ensemble avec une _MEDIUM. Est-ce que ça existe?",
            "Nous sommes 4 musiciens (_MEDIUM, _MEDIUM, _MEDIUM, et _MEDIUM). Vous auriez des partitions de _AGENT que l'on pourrait jouer",
            "œuvres de _AGENT",
            "Avez-vous des œuvres d'_AGENT ?",

            # FORMATIONS
            "Je cherche des _FORMATION avec une _MEDIUM.",
            "Avez-vous des _FORMATION _LEVEL_SENTENCE au _MEDIUM et au _MEDIUM ?   ",
            "Je cherche des _FORMATION _LEVEL_SENTENCE au _MEDIUM",
            "Un morceau pour un _FORMATION de _MEDIUM ",
            "Je cherche une partition pour un _FORMATION de _MEDIUM",
            "Partitions pour _FORMATION de _MEDIUM et _MEDIUM.",
            "Quelles sont les partitions en stock pour _FORMATION de musiciens?",
            "Je recherche des _FORMATION pour _MEDIUM",
            "Je recherche des _FORMATION _MEDIUM _MEDIUM.",
            "Je voudrais trouver des arrangements de _GENRE pour _FORMATION à _MEDIUM",
            "Je cherche des partitions pour _FORMATION à _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION à _MEDIUM",

            # LOCATIONS / PERIOD
            "Je dirige un _MEDIUM et je cherche des partitions de musique _LOCATION",
            "Est-ce que vous auriez de l’_PERIOD _LOCATION, mais en notation occidentale ?",
            "Je recherche des partitions de _GENRE _LOCATION pour _MEDIUM",
            "J’aimerai accéder à un recueil de partitions de _GENRE _LOCATION de la fin du _PERIOD.",
            "J’aimerai accéder à un recueil de partitions de la _PERIOD",
            "Trouve des partitions de la _PERIOD pour _MEDIUM",
            "Des fac- similés de partitions de musique _PERIOD _LOCATION",
            "Vous avez des partitions de musique _LOCATION ?",
            "Qu'est-ce qui existe pour _FORMATION en musique _PERIOD ?",
            "Je souhaite accéder à des partitions pour _MEDIUM composées en _LOCATION au _PERIOD",
            "Des partitions de musique _PERIOD pour _MEDIUM",
            "Des partitions pour choeurs de musique de la _PERIOD",
            "Des partitions pour choeurs du _PERIOD",
            "Des partitions de musique du _PERIOD pour _MEDIUM",
            "Je veux des partitions du _PERIOD",
            "Quelles partitions de la fin du _PERIOD pour trois _MEDIUM?",
            "Des partitions pour _FORMATION avec _MEDIUM du répertoire _GENRE",
            "Je cherche des _MEDIUM du _PERIOD",
            "Je recherche des pièces pour _MEDIUM en musique _PERIOD",
            "Nous sommes deux _MEDIUM et nous cherchons un morceau de _GENRE à jouer. ",
            "je cherche des partitions de _GENRE pour _FORMATION [à corde]{\"entity\": \"medium\"}",
            "je cherche des partitions de _PERIOD pour 2 _MEDIUM 1 _MEDIUM",
            "Je cherche des partitions de musique _LOCATION pour _MEDIUM et _MEDIUM",
            "Je cherche des scores pour groupe de _GENRE",
            "Partitions de musique _LOCATION",
            "Partitions de musique _LOCATION svp",
            "Partitions de musique du _PERIOD",
            "Je recherche des arrangements/transcriptions de musiques de _GENRE (en tout genre)",
        ],
        "entities": [
            ([preprocess_entity(i) for sublist in list(iaml.values()) + list(mimo.values()) for i in sublist], "_MEDIUM"),
            ([preprocess_entity(i) for sublist in list(level_sentences.values()) for i in sublist], "_LEVEL_SENTENCE"),
            ([preprocess_entity(i) for sublist in list(level_worded.values()) for i in sublist], "_LEVEL_WORDED"),
            ([preprocess_entity(i) for sublist in list(level_timing.values()) for i in sublist], "_LEVEL_TIMING"),
            ([preprocess_entity(i) for sublist in list(formations.values()) for i in sublist], "_FORMATION"),
            ([preprocess_entity(i) for sublist in list(periods.values()) for i in sublist], "_PERIOD"),
            ([preprocess_entity(i) for sublist in list(locations.values()) for i in sublist], "_LOCATION"),
            (GENRES, "_GENRE"),
            (AGENTS, "_AGENT"),
        ],
    },
}

keyword_to_ent_type = {
    "_MEDIUM": "medium",
    "_LEVEL_SENTENCE": "level",
    "_LEVEL_WORDED": "level",
    "_LEVEL_TIMING": "level",
    "_GENRE": "genre",
    "_AGENT": "agent",
    "_FORMATION": "formation",
    "_PERIOD": "period",
    "_LOCATION": "location",
}

def entities_round_robin(entities):
    """
    Create an iterable from n lists of entities, which will perform round-robin iterations
    on all elements.
    """
    # Make
    len_entities = [len(e[0]) for e in entities]
    entity_iterators = []
    entity_keywords = []
    for ent_list, keyword in entities:
        if len(ent_list) == max(len_entities):
            # if ent is the longest list, we can append it directy
            entity_iterators.append(ent_list)
            entity_keywords.append(keyword)
        else:
            # if ent is not the longest, we make it a cycle to avoir stopiteration errors
            entity_iterators.append(itertools.cycle(ent_list))
            entity_keywords.append(keyword)
    return zip(*entity_iterators), entity_keywords


if __name__ == "__main__":
    with open("data/nlu/nlu_intents.yml", "w") as f:
        f.write("version: \"2.0\"\n\nnlu:")
        for intent, data in raw_sentences.items():
            f.write(f"\n- intent: {intent}\n  examples: |\n")
            if len(data["entities"]) == 0:
                for sent in data["sentences"]:
                    f.write(f"    - {sent}\n")
                continue
            entity_generator, entity_keywords = entities_round_robin(data["entities"])
            cycle_sentences = itertools.cycle(data['sentences'])
            for entity_tuples in entity_generator:
                # Replace the keyword with the entity 
                sent = next(cycle_sentences)
                for i, entity in enumerate(entity_tuples):
                    sent = sent.replace(entity_keywords[i], f"[{entity}]{{\"entity\": \"{keyword_to_ent_type[entity_keywords[i]]}\"}}")
                f.write(f"    - {sent}\n")
            