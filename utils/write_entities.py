from medias_synonyms import iaml, mimo
from levels_synonyms import all_levels
from genres_synonyms import genres
from agents_synonyms import agents
from periods_synonyms import periods
from locations_synonyms import locations
from formations_synonyms import formations
import string

def preprocess_entity(entity: str, lower=True):
    # Lower
    if lower:
        entity = entity.lower()
    # Strip punctuation
    exclude = string.punctuation.replace("-", "")
    exclude = exclude.replace("'", "")
    exclude = exclude.replace(".", "")
    exclude += "«»"
    for ch in exclude:
        entity = entity.replace(ch, "_")
    entity = entity.split("_")[0].strip()
    return entity

def print_synonyms(synonyms: dict, filename: str):
    """Print to stdout all the given synonyms, with the correct rasa nlu.yml file format."""
    with open(f"data/nlu/{filename}.yml", "w") as f:
        f.write(f"version: \"2.0\"\n\nnlu:\n")
        for k, v in synonyms.items():
            f.write(f"\n- synonym: \"{k}\"\n  examples: |\n")
            for i in v:
                f.write(f"    - {preprocess_entity(i)}\n")

if __name__ == "__main__":
    print_synonyms(iaml, "nlu_entities_iaml")
    print_synonyms(mimo, "nlu_entities_mimo")
    print_synonyms(genres, "nlu_entities_genres")
    print_synonyms(agents, "nlu_entities_agents")
    print_synonyms(formations, "nlu_entities_formations")
    print_synonyms(periods, "nlu_entities_periods")
    print_synonyms(locations, "nlu_entities_locations")
    print_synonyms(all_levels, "nlu_entities_level")