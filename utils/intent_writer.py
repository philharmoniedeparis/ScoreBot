import itertools
import numpy as np

from medias_synonyms import iaml, mimo
from levels_synonyms import level_sentences, level_timing, level_worded
from genres_synonyms import genres
from agents_synonyms import agents
from formations_synonyms import formations
from periods_synonyms import periods
from locations_synonyms import locations
from work_names_synonyms import work_names
from write_entities import preprocess_entity


GENRES = np.repeat([preprocess_entity(i) for sublist in list(genres.values()) for i in sublist], 3)

# AGENTS: Repeat the 10 first agents 5 times because they are VIPs
# AGENTS_VIP = np.repeat([preprocess_entity(sublist[0], lower=False) for sublist in list(agents.values())[:10]], 10)
# AGENTS_FILLING = np.random.choice([preprocess_entity(i, lower=False) for sublist in list(agents.values()) for i in sublist], len(GENRES) - len(AGENTS_VIP))
# AGENTS = AGENTS_VIP.tolist() + AGENTS_FILLING.tolist()
AGENTS = []
for ix, sublist in enumerate(list(agents.values())):
    for val in sublist:
        val = val.split(" ")[-1] if not ix % 2 else val
        AGENTS.append(preprocess_entity(val, lower=False))
AGENTS = np.random.choice(AGENTS, len(GENRES))

raw_sentences = {
    "get_sheet_music_by_casting": {
        "sentences": [
            # MEDIUM
            "_MEDIUM",
            "un _MEDIUM",
            "_MEDIUM _MEDIUM",
            "_MEDIUM _MEDIUM",
            "_MEDIUM _MEDIUM",
            "_MEDIUM _MEDIUM",
            "_MEDIUM, _MEDIUM",
            "_MEDIUM et _MEDIUM",
            "_MEDIUM _MEDIUM _MEDIUM",
            "_MEDIUM, _MEDIUM et _MEDIUM",
            "_MEDIUM, _MEDIUM _MEDIUM _MEDIUM",
            "deux _MEDIUM",
            "deux _MEDIUM",
            "trois _MEDIUM",
            "2 _MEDIUM",
            "3 _MEDIUM",
            "un _MEDIUM et un _MEDIUM",
            "deux _MEDIUM plus trois _MEDIUM",
            "Je cherche une partition pour un _MEDIUM",
            "Je cherche une partition pour _MEDIUM",
            "Je cherche une partition pour deux _MEDIUM ou plus",
            "Je cherche une partition avec deux _MEDIUM ou plus",
            "Quelles partitions avez-vous pour trois _MEDIUM et un _MEDIUM ?",
            "Quelles partitions avez-vous avec trois _MEDIUM et un _MEDIUM ?",
            "Je suis _MEDIUM et je cherche des partitions pour _MEDIUM et d'autres _MEDIUM.",
            "Pour un _MEDIUM, un _MEDIUM, et quatre _MEDIUM, quelles partitions?",
            "Je recherche une partition pour _MEDIUM et _MEDIUM ",
            "Avez-vous un morceau simple à me conseiller pour _MEDIUM et _MEDIUM ? ",
            "Avez-vous un morceau simple à me conseiller avec _MEDIUM et _MEDIUM ? ",
            "Je cherche des partitions de grands classiques, en version simplifiée, à jouer au _MEDIUM.",
            "Pourrais-je voir la liste de toutes vos partitions pour _MEDIUM ?",
            "Pourrais-je avoir la liste de toutes vos partitions pour _MEDIUM ?",
            "Pourrais-je avoir la liste de toutes vos partitions avec _MEDIUM ?",
            "Pourrais-je voir la liste de vos partitions pour _MEDIUM",
            "Donnez-moi la liste de vos partitions pour _MEDIUM.",
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
            "Avez-vous des partitions _LEVEL_SENTENCE pour _MEDIUM ?",
            "Avez-vous des partitions _LEVEL_SENTENCE pour _MEDIUM ?",
            "Avez-vous des partitions _LEVEL_SENTENCE avec _MEDIUM ?",
            "Je cherche des chansons _LEVEL_SENTENCE à 2 _MEDIUM?",
            "est-ce qu'il y a des arrangements de musique de _GENRE pour jouer avec des élèves _LEVEL_WORDED de conservatoire?",
            "Je veux de la musique de _GENRE pour mes élèves _LEVEL_WORDED",
            "je fais du _MEDIUM depuis _LEVEL_TIMING et je cherche des partitions à mon niveau.",
            "Je cherche quelque chose à jouer pour 2 _MEDIUM et une _MEDIUM avec un niveau _LEVEL_WORDED",
            "Je cherche des partitions pour musiciens avec un niveau _LEVEL_WORDED jouant du _MEDIUM et du _MEDIUM.",
            "Donnez moi les partitions avec un _MEDIUM et une _MEDIUM _LEVEL_SENTENCE.",
            "Liste partitions deux _MEDIUM pour musicien avec niveau _LEVEL_WORDED",
            "Quels sont les morceaux jouables par un groupe de 2 _MEDIUM ayant un niveau _LEVEL_WORDED?",
            "Je cherche des partitions pour musiciens jouant du _MEDIUM et du _MEDIUM depuis _LEVEL_TIMING.",
            "Je suis _MEDIUM et je cherche des partitions pour _MEDIUM pour élèves pratiquant depuis _LEVEL_TIMING. ",
            "Je suis _MEDIUM et je cherche des partitions avec _MEDIUM pour élèves pratiquant depuis _LEVEL_TIMING. ",
            "Je cherche des _FORMATION avec une _MEDIUM _LEVEL_SENTENCE.",
            "Avez-vous une idée de morceau pour _MEDIUM et _MEDIUM  _LEVEL_SENTENCE? ",
            "Avez-vous une idée de morceau avec _MEDIUM et _MEDIUM  _LEVEL_SENTENCE? ",
            "Avez-vous des _FORMATION à jouer au _MEDIUM et au _MEDIUM _LEVEL_SENTENCE ?  ",
            "Un morceau pour un _FORMATION de _MEDIUM ayant _LEVEL_TIMING d'expérience",
            "Je recherche des _FORMATION pour _MEDIUM de niveau _LEVEL_WORDED",
            "Je recherche des _FORMATION _MEDIUM _MEDIUM _LEVEL_SENTENCE.",
            "Partition graphique pour _MEDIUM pour niveau _LEVEL_WORDED",
            "Je voudrais trouver des partitions pour 3 _MEDIUM, 2 _MEDIUM, 1 _MEDIUM et une _MEDIUM _LEVEL_SENTENCE",
            "Je voudrais trouver des partitions pour trois _MEDIUM, deux _MEDIUM, un _MEDIUM et une _MEDIUM",
            "Je veux des partitions pour 1 _MEDIUM, 2 _MEDIUM, 3 _MEDIUM et aussi 1 _MEDIUM",
            "partitions pour 3 _MEDIUM 2 _MEDIUM, 1 _MEDIUM et 1 _MEDIUM",
            "Je cherche des partitions pour _MEDIUM pour des musiciens avec un niveau _LEVEL_WORDED",
            "Je souhaite trouver des œuvres pour _MEDIUM _LEVEL_SENTENCE",
            "Je cherche des partitions pour _MEDIUM _LEVEL_SENTENCE",
            "Une partition pour _MEDIUM _LEVEL_SENTENCE",
            "Une partition pour _MEDIUM _LEVEL_SENTENCE ?",
            "partition pour _MEDIUM _LEVEL_SENTENCE",
            "Une partition pour _MEDIUM _LEVEL_WORDED",
            "partition _MEDIUM _LEVEL_SENTENCE",

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
            "Je dirige un _MEDIUM et je cherche des partitions de musique _GENRE.",
            "Je dirige un _MEDIUM et je cherche de la _GENRE.",
            "Je joue du _MEDIUM et je cherche de la _GENRE.",
            "Je suis un _MEDIUM et je cherche du _GENRE.",
            "Est-ce que vous auriez de la _GENRE, mais en notation occidentale ?",
            "Je recherche des partitions de _GENRE pour _MEDIUM",
            "Je recherche des partitions de _GENRE avec _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION à _MEDIUM",
            "Donne moi la liste des morceaux de _GENRE destinés à _FORMATION à _MEDIUM",
            "Je veux les partitions de _GENRE pour _FORMATION _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION de _MEDIUM",
            "Je cherche des partitions de _GENRE pour _FORMATION _MEDIUM",
            "Je recherche des partitions d'[opéra] {\"entity\": \"genre\"} pour [quatuors]{\"entity\": \"formation\"} [à corde]{\"entity\": \"medium\"}",
            "Je cherche des partitions de [jazz] {\"entity\": \"genre\"} pour _FORMATION [à vent]{\"entity\": \"medium\"}",
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
            "Des partitions de _GENRE avec _MEDIUM",
            "Des partitions pour _MEDIUM du _GENRE",
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
            "_FORMATION de _MEDIUM de _AGENT",
            "_FORMATION d'_MEDIUM d'_AGENT",
            "_FORMATION de _MEDIUM d'_AGENT",
            "_FORMATION de _MEDIUM _AGENT",
            "_FORMATION pour _MEDIUM d'_AGENT",
            "_FORMATION avec _MEDIUM de _AGENT",
            "Je veux un _FORMATION avec _MEDIUM de _AGENT",
            "Je cherche un _FORMATION avec _MEDIUM de _AGENT",
            "_FORMATION pour _MEDIUM écrite par _AGENT",
            "Donne moi les partitions pour une _MEDIUM et un _MEDIUM de _AGENT _LEVEL_SENTENCE.",
            "Je cherche la partition d'une oeuvre _GENRE de _AGENT",
            "Je cherche la partition d'une oeuvre de _AGENT _LEVEL_SENTENCE",
            "Est-ce que vous avez les sonates de _AGENT d’après-guerre ?",
            "Une collection intégrale des oeuvres d'_AGENT",
            "Une partition de _MEDIUM de la 5e Symphonie de _AGENT",
            "Les transcriptions de solos de _AGENT",
            "Avez-vous des partitions d'_AGENT de niveau _LEVEL_WORDED pour _MEDIUM et _MEDIUM ? ",
            "Avez-vous des partitions _MEDIUM écrites par _AGENT ?",
            "Avez-vous des partitions pour _MEDIUM écrites par _AGENT ?",
            "Avez-vous des partitions avec _MEDIUM écrites par _AGENT _LEVEL_SENTENCE?",
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
            "Je cherche des partitions de _AGENT.",
            "Je cherche des partitions d'_AGENT",

            "Quelles partitions de _AGENT avez-vous pour trois _MEDIUM et un _MEDIUM ?",
            "Pour un _MEDIUM, un _MEDIUM, et quatre _MEDIUM, quelles partitions de _AGENT?",
            "Je recherche une partition d'_AGENT pour _MEDIUM et _MEDIUM  eleves depuis _LEVEL_TIMING",
            "Avez-vous un morceau simple de _AGENT à me conseiller pour _MEDIUM et _MEDIUM ? ",
            "Je recherche une oeuvre _GENRE composee par _AGENT que l'on pourrait jouer avec un _MEDIUM, une _MEDIUM et un _MEDIUM",
            "Je cherche des partitions de grands classiques de _AGENT, en version simplifiée, à jouer au _MEDIUM.",
            "Je voudrais trouver des arrangements de _GENRE de _AGENT pour _MEDIUM",
            "Je voudrais des jigs pour _MEDIUM crees par _AGENT",
            "_MEDIUM tab",
            "Je cherche les partitions du _AGENT pour ensemble avec une _MEDIUM. Est-ce que ça existe?",
            "Nous sommes 4 musiciens (_MEDIUM, _MEDIUM, _MEDIUM, et _MEDIUM). Vous auriez des partitions de _AGENT que l'on pourrait jouer",
            "œuvres de _AGENT",
            "Avez-vous des œuvres d'_AGENT ?",
            "je cherche des _GENRE de _AGENT",
            "Je cherche un _GENRE de _AGENT",
            "Je cherche un _GENRE d' _AGENT",
            "donne moi des _GENRE d'_AGENT",
            "je veux les _GENRE écrits par _AGENT",

            # FORMATIONS
            "_FORMATION de _MEDIUM",
            "_FORMATION de _MEDIUM.",
            "_FORMATION de _MEDIUM?",
            "_FORMATION d'_MEDIUM",
            "_FORMATION avec _MEDIUM",
            "_FORMATION pour _MEDIUM",
            "Je cherche un _FORMATION _MEDIUM _MEDIUM",
            "Je cherche une _FORMATION _MEDIUM _MEDIUM",
            "Je cherche une _FORMATION 2 _MEDIUM 1 _MEDIUM",
            "Je cherche un _FORMATION avec _MEDIUM et _MEDIUM",
            "Je cherche un _FORMATION pour un _MEDIUM et deux _MEDIUM",
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
            "Je voudrais trouver des arrangements de musique _GENRE pour _FORMATION _MEDIUM",

            # LOCATIONS / PERIOD
            "musique d'_LOCATION_NOUN",
            "musiques d'_LOCATION_NOUN",
            "partition d'_LOCATION_NOUN",
            "partitions d'_LOCATION_NOUN",
            "musique de la _LOCATION_NOUN",
            "musiques de la _LOCATION_NOUN",
            "partition de la _LOCATION_NOUN",
            "partition du _LOCATION_NOUN",
            "musique du _LOCATION_NOUN",
            "Je dirige un _MEDIUM et je cherche des partitions de musique de la _LOCATION_NOUN",
            "Je dirige un _MEDIUM et je cherche des partitions de musique composée en _LOCATION_NOUN",
            "Je dirige un _MEDIUM et je cherche de la musique composée au _LOCATION_NOUN",
            "Je dirige un _MEDIUM et j'aimerais trouver de la musique de _LOCATION_NOUN",
            "Je suis le directeur d'un _MEDIUM et je voudrais des partitions de musique d'_LOCATION_NOUN",
            "Je m'occupe d'un _MEDIUM et je veux des partitions du _LOCATION_NOUN",
            "Est-ce que vous auriez de la _PERIOD de la _LOCATION_NOUN, mais en notation occidentale ?",
            "Je cherche des _MEDIUM du _PERIOD",
            "Je cherche des _MEDIUM a capella du _PERIOD",
            "Ça existe les partitions de la _PERIOD d'_LOCATION_NOUN ?",
            "Ca existe les partitions du _PERIOD écrite en _LOCATION_NOUN ?",
            "Ca existe les partitions du _PERIOD écrite au _LOCATION_NOUN ?",
            "Est-ce que vous avez de l’_PERIOD de _LOCATION_NOUN ?",
            "Est-ce qu'il existe de la musique de la _PERIOD du _LOCATION_NOUN ?",
            "Je recherche des partitions de _GENRE de la _LOCATION_NOUN pour _MEDIUM",
            "Je veux des partitions de _GENRE du _LOCATION_NOUN avec _MEDIUM a capella",
            "Je voudrais de la musique de _GENRE d'_LOCATION_NOUN de _MEDIUM",
            "J'aimerais trouver du _GENRE de _LOCATION_NOUN pour _MEDIUM",
            "J’aimerai accéder à des partitions de _GENRE de la _LOCATION_NOUN de la fin du _PERIOD.",
            "Je veux trouver un recueil de musique de _GENRE d'_LOCATION_NOUN du début du _PERIOD.",
            "Ou trouver un recueil de _GENRE du _LOCATION_NOUN du _PERIOD.",
            "Avez-vous un recueil de musique de _GENRE de _LOCATION_NOUN de _PERIOD.",
            "Recueil de partitions de la _PERIOD",
            "Trouve de la musique de la _PERIOD pour _MEDIUM",
            "Trouve-moi des partitions de _PERIOD pour _MEDIUM",
            "Je veux des partitions du _PERIOD avec _MEDIUM",
            "Trouve de la musique d'_PERIOD pour _MEDIUM",
            "Trouve des partitions du _PERIOD de _MEDIUM",
            "Des fac- similés de partitions de musique de la _PERIOD du _LOCATION_NOUN",
            "Des facsimilés de musique de la _PERIOD d'_LOCATION_NOUN",
            "Je cherche des partitions du _PERIOD de la _LOCATION_NOUN",
            "Des fac- similés de partitions de musique de _PERIOD de _LOCATION_NOUN",
            "Vous avez des partitions de musique de _LOCATION_NOUN ?",
            "Avez-vous des partitions de la _LOCATION_NOUN ?",
            "Est-ce que vous avez de la musique du _LOCATION_NOUN ?",
            "Qu'est-ce que vous avez en musique d' _LOCATION_NOUN ?",
            "Qu'est-ce qui existe pour _FORMATION en musique de la _PERIOD ?",
            "Avez-vous des partitions pour _FORMATION en musique _PERIOD ?",
            "Je souhaite accéder à des partitions pour _MEDIUM composées en _LOCATION_NOUN au _PERIOD",
            "Des partitions de musique _PERIOD pour _MEDIUM",
            "Des partitions pour _MEDIUM a capella de musique de la _PERIOD",
            "Des partitions pour _MEDIUM de la _PERIOD",
            "Des partitions pour _MEDIUM du _PERIOD",
            "Des partitions pour _MEDIUM de musique du _PERIOD",
            "Des partitions de musique du _PERIOD pour _MEDIUM",
            "Des partitions de musique de la _PERIOD pour _MEDIUM",
            "Je veux des partitions du _PERIOD",
            "Je veux des partitions de la _PERIOD",
            "Quelles partitions de la fin du _PERIOD pour trois _MEDIUM?",
            "Quelles partitions de la fin de la _PERIOD pour trois _MEDIUM?",
            "Des partitions pour _FORMATION avec _MEDIUM du répertoire _GENRE",
            "Je cherche des _GENRE de la _PERIOD",
            "Je cherche des _GENRE du _PERIOD",
            "Je recherche des pièces pour _MEDIUM en musique _PERIOD",
            "Nous sommes deux _MEDIUM et nous cherchons un morceau de _GENRE à jouer. ",
            "je cherche des partitions de _GENRE pour _FORMATION [à corde]{\"entity\": \"medium\"}",
            "je cherche des partitions de _PERIOD pour 2 _MEDIUM 1 _MEDIUM",
            "je cherche des partitions de la _PERIOD pour 2 _MEDIUM 1 _MEDIUM",
            "je cherche des partitions du _PERIOD pour 2 _MEDIUM 1 _MEDIUM",
            "Je cherche des partitions de musique _LOCATION_NOUN pour _MEDIUM et _MEDIUM",
            "Je cherche des scores pour groupe de _GENRE",
            "Partitions de musique du _LOCATION_NOUN",
            "Partitions de musique de la _LOCATION_NOUN",
            "Vous avez des partitions de musique de la _LOCATION_NOUN ?",
            "Vous avez des partitions de musique de l'_LOCATION_NOUN",
            "Partitions de musique d'_LOCATION_NOUN",
            "Partitions de musique de _LOCATION_NOUN",
            "Partitions de musique _LOCATION_NOUN svp",
            "Partitions de musique du _PERIOD",
            "_GENRE du _PERIOD",
            "je veux des _GENRE du _PERIOD",
            "_GENRE de la _PERIOD",
            "Je recherche des arrangements/transcriptions de musiques de _GENRE (en tout genre)",

            # LOCATION ADJECTIVE
            "musique _LOCATION_ADJECTIVE",
            "musiques _LOCATION_ADJECTIVE",
            "partition _LOCATION_ADJECTIVE",
            "partitions _LOCATION_ADJECTIVE",
            "Vous avez des partitions de musique _LOCATION_ADJECTIVE ?",
            "Vous avez des partitions _LOCATION_ADJECTIVE ?",
            "Vous avez des musiques _LOCATION_ADJECTIVE ?",
            "Vous avez de la musique _LOCATION_ADJECTIVE ?",
            "Partitions de musique _LOCATION_ADJECTIVE",
            "Je veux des partitions de musique _LOCATION_ADJECTIVE",
            "Donnez moi des partitions de musique _LOCATION_ADJECTIVE",
            "Quelles sont les partitions de musique _LOCATION_ADJECTIVE",
            "Je veux accéder à de la musique _LOCATION_ADJECTIVE",
            "Est-ce que tu as de la musique _LOCATION_ADJECTIVE",
            "Partitions de musique _LOCATION_ADJECTIVE",
            "Je dirige un _MEDIUM et je cherche des partitions de musique _LOCATION_ADJECTIVE",
            "Je suis le directeur d'un _MEDIUM et je voudrais des partitions de musique _LOCATION_ADJECTIVE",
            "Est-ce que vous auriez de la _LOCATION_ADJECTIVE, mais en notation occidentale ?",
            "Ca existe les partitions _LOCATION_ADJECTIVE de la _PERIOD ?",
            "Ca existe les partitions _LOCATION_ADJECTIVE de la période _PERIOD ?",
            "Ca existe les partitions _LOCATION_ADJECTIVE de l'époque _PERIOD ?",
            "Est-ce que vous avez de l’_PERIOD _LOCATION_ADJECTIVE ?",
            "Est-ce qu'il existe de la musique de la _PERIOD _LOCATION_ADJECTIVE ?",
            "Je recherche des partitions de _GENRE _LOCATION_ADJECTIVE pour _MEDIUM",
            "Je veux trouver un recueil de musique de _GENRE _LOCATION_ADJECTIVE du début du _PERIOD.",
            "recueil de _GENRE _LOCATION_ADJECTIVE du _PERIOD",
            "recueil de _GENRE _LOCATION_ADJECTIVE de l'époque _PERIOD",
            "recueil de _GENRE _LOCATION_ADJECTIVE de la période _PERIOD",
            "un recueil de _GENRE de l'époque _PERIOD",
            "Ou trouver un recueil de _GENRE _LOCATION_ADJECTIVE du _PERIOD.",
            "Ou trouver un recueil de _GENRE _LOCATION_ADJECTIVE de l'époque _PERIOD.",
            "Ou trouver un recueil de _GENRE _LOCATION_ADJECTIVE de la période _PERIOD.",
            "Recueil de partitions _LOCATION_ADJECTIVE",
            "Trouve de la musique _LOCATION_ADJECTIVE pour _MEDIUM",
            "Trouve-moi des partitions _LOCATION_ADJECTIVE pour _MEDIUM",
            "Je veux des partitions _LOCATION_ADJECTIVE avec _MEDIUM",
            "Trouve de la musique _LOCATION_ADJECTIVE pour _MEDIUM",
            "Est-ce que vous avez de la musique _LOCATION_ADJECTIVE ?",
            "Partitions de musique _LOCATION_ADJECTIVE",
            "Liste partitions de musique _LOCATION_ADJECTIVE",
            "musique _LOCATION_ADJECTIVE ?",
            "Partitions de musique _LOCATION_ADJECTIVE",
            "Partitions de musique _LOCATION_ADJECTIVE svp",
            "Quelles partitions de musique _LOCATION_ADJECTIVE",
            "Je veux des partitions de musique _LOCATION_ADJECTIVE svp",
            "Vous avez des partitions de musique _LOCATION_ADJECTIVE ?",
            "Vous avez des partitions de musique _LOCATION_ADJECTIVE",
            "Donne moi une partition d'une oeuvre _LOCATION_ADJECTIVE avec un _MEDIUM",
            "Donne moi une partition _LOCATION_ADJECTIVE avec _MEDIUM",
            "Je veux une oeuvre _LOCATION_ADJECTIVE pour _MEDIUM",
            "Je veux une partition de musique _LOCATION_ADJECTIVE pour _MEDIUM",
            "Je veux une partition de musique _LOCATION_ADJECTIVE",
            "partition de musique _LOCATION_ADJECTIVE",
            "musique _LOCATION_ADJECTIVE",


            # WORK_NAME
            "Je cherche la partition de la _WORK_NAME de _AGENT",
            "Vous avez les partitions de _WORK_NAME ?",
            "Différentes versions du _WORK_NAME de _AGENT",
            "Une transcription du _WORK_NAME de _AGENT pour _MEDIUM",
            "Une transcription de _WORK_NAME pour _MEDIUM",
            "Une transcription de la _WORK_NAME pour _MEDIUM",
            "transcription de _WORK_NAME pour un _MEDIUM",
            "Donne moi une transcription de la _WORK_NAME pour _MEDIUM",
            "Une partition de _WORK_NAME pour _MEDIUM",
            "partition de _WORK_NAME de _MEDIUM",
            "Une partition du _WORK_NAME de _AGENT",
            "Une partition de la _WORK_NAME d'_AGENT",
            "Partition de _WORK_NAME _AGENT",
            "La _WORK_NAME de _AGENT",
            "_WORK_NAME de _AGENT",
            "Le _WORK_NAME de _AGENT",
            "_WORK_NAME d'_AGENT",
            "La _WORK_NAME d'_AGENT",
            "Le _WORK_NAME d'_AGENT",
            "_WORK_NAME du _AGENT",
            "La _WORK_NAME du _AGENT",
            "Une partition du _WORK_NAME",
            "Partition du _WORK_NAME",
            "Partition de _WORK_NAME",
            "Partition de _WORK_NAME",
            "l'oeuvre la _WORK_NAME",
            "L'oeuvre le _WORK_NAME",
            "L'oeuvre le _WORK_NAME de _AGENT",
            "L'oeuvre la _WORK_NAME d'_AGENT",
            "Une partition d'_MEDIUM de la _WORK_NAME de _AGENT",
            "Une partition d'[orchestre]{\"entity\": \"medium\"} de la _WORK_NAME de _AGENT",
            "Une partition pour [orchestre]{\"entity\": \"medium\"} de la _WORK_NAME de _AGENT",
            "Je veux une partition d'_MEDIUM de la _WORK_NAME de _AGENT",
            "Une partition d'_MEDIUM de _WORK_NAME d'_AGENT",
            "Je veux une partition d'_MEDIUM, de _WORK_NAME, d'_AGENT",
            "Donne-moi une partition d'_MEDIUM de la _WORK_NAME d'_AGENT",
            "Une partition pour _MEDIUM du _WORK_NAME d'_AGENT",
            "Une partition de _WORK_NAME d'_AGENT pour _MEDIUM",
            "Une partition du _WORK_NAME d'_AGENT de _MEDIUM",
            "Je veux une partition de _WORK_NAME d'_AGENT de _MEDIUM",
            "Donne-moi une partition de la _WORK_NAME d'_AGENT de _MEDIUM",
            "Partition d'_MEDIUM de _WORK_NAME d'_AGENT",
            "Partition d'_MEDIUM de la _WORK_NAME de _AGENT",
            "Une partition de _MEDIUM du _WORK_NAME de _AGENT",
            "Partition de _MEDIUM de _WORK_NAME d'_AGENT",
            "Quelle partition d'_MEDIUM de _WORK_NAME de_AGENT?",
            "Une partition pour _MEDIUM du _WORK_NAME de _AGENT",
            "Partition de _MEDIUM de _WORK_NAME d'_AGENT",
            "Je veux une transcription de la _WORK_NAME pour _MEDIUM",
            "Partition de _WORK_NAME pour _MEDIUM",
            "Différentes versions de la _WORK_NAME de _AGENT",
            "Je suis institutrice et souhaiterais faire apprendre à mes élèves une chanson traditionnelle : _WORK_NAME.",
            "Je cherche les paroles d’une chanson pour _LEVEL_SENTENCES qui est connue sous plusieurs noms : '_WORK_NAME', '_WORK_NAME' ou '_WORK_NAME'.",
            "Je cherche la partition gratuite du _WORK_NAME",
            "Je veux une partition de la réduction pour _MEDIUM de l'ouverture de _WORK_NAME.",
            "Je cherche une partition de la réduction pour [piano]{\"entity\": \"medium\"} de l'ouverture de  _WORK_NAME.",
            "Je veux une partition de la réduction pour _MEDIUM d'ouverture de _WORK_NAME.",
            "Je cherche une partition de la réduction pour [piano]{\"entity\": \"medium\"} de _WORK_NAME.",
            "partition de réduction pour _MEDIUM de l'ouverture de  _WORK_NAME.",
            "Je veux la partition de la réduction pour _MEDIUM de la _WORK_NAME.",
            "Je veux la partition pour _MEDIUM du _WORK_NAME.",
            "Partition pour _MEDIUM de _WORK_NAME.",
            "Je cherche une partition de la réduction pour _MEDIUM du _WORK_NAME.",
            "Donne moi une partition de la réduction pour _MEDIUM de l'ouverture du _WORK_NAME.",
            "Je cherche la partition de la musique de la _WORK_NAME",
            "Où trouver le conducteur de _WORK_NAME de _AGENT ?",
            "je cherche la partition de la version pour _MEDIUM des _WORK_NAME de _AGENT",
            "je veux la version pour _MEDIUM de la _WORK_NAME de _AGENT",
            "la partition des _WORK_NAME d'_AGENT",
        ],
        "entities": {
            "_MEDIUM": [preprocess_entity(i) for sublist in list(iaml.values()) + list(mimo.values()) for i in sublist],
            "_LEVEL_SENTENCE": [preprocess_entity(i) for sublist in list(level_sentences.values()) for i in sublist],
            "_LEVEL_WORDED": [preprocess_entity(i) for sublist in list(level_worded.values()) for i in sublist],
            "_LEVEL_TIMING": [preprocess_entity(i) for sublist in list(level_timing.values()) for i in sublist],
            "_FORMATION": [preprocess_entity(i) for sublist in list(formations.values()) for i in sublist],
            "_PERIOD": [preprocess_entity(i) for sublist in list(periods.values()) for i in sublist],
            "_LOCATION_NOUN": [preprocess_entity(i, lower=False) for sublist in list(locations.values()) for i in sublist],
            "_WORK_NAME": [preprocess_entity(i, lower=False) for sublist in list(work_names.values())[:100] for i in sublist],
            "_LOCATION_ADJECTIVE": [preprocess_entity(sublist[2]) for sublist in list(locations.values())[:50]],
            "_GENRE": GENRES,
            "_AGENT": AGENTS,
        },
    },
}

keyword_to_ent_type = {
    "_MEDIUM": "medium",
    "_LEVEL_SENTENCE": "level",
    "_LEVEL_WORDED": "level",
    "_LEVEL_TIMING": "level",
    "_GENRE": "genre",
    "_AGENT": "agent",
    "_WORK_NAME": "work_name",
    "_FORMATION": "formation",
    "_PERIOD": "period",
    "_LOCATION_NOUN": "location",
    "_LOCATION_ADJECTIVE": "location",
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
            entities = {entity_type: itertools.cycle(entity_list) for entity_type, entity_list in data["entities"].items()}
            for i in range(15):
                for sent in data["sentences"]:
                    for entity_keyword in entities.keys():
                        if entity_keyword in sent:
                            ent = next(entities[entity_keyword])
                            sent = sent.replace(entity_keyword, f"[{ent}]{{\"entity\": \"{keyword_to_ent_type[entity_keyword]}\"}}")
                    f.write(f"    - {sent}\n")
            