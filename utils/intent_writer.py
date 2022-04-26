import itertools

from medias_synonyms import medias
from write_entities import preprocess_entity


raw_sentences = {
    "get_sheet_music_by_casting": {
        "sentences": [
            "Donnez moi les partitions avec un _MEDIUM et une _MEDIUM.",
            "Quelles partitions avez-vous pour trois _MEDIUM et un _MEDIUM ?",
            "Liste partitions deux _MEDIUM",
            "Pour un _MEDIUM, un _MEDIUM, et quatre _MEDIUM, quelles partitions?",
            "Quels sont les morceaux jouables par un groupe de 2 _MEDIUM?"
        ],
        "entities": [
            ([preprocess_entity(i) for sublist in medias.values() for i in sublist], "_MEDIUM"),
        ],
    },
}

keyword_to_ent_type = {
    "_MEDIUM": "medium",
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
    with open("data/nlu/nlu_philharmonie_intents.yml", "w") as f:
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
            