from medias_synonyms import medias
import string

def preprocess_entity(entity: str):
    # Lower
    entity = entity.lower()
    # Strip punctuation
    exclude = string.punctuation.replace("-", "")
    exclude = exclude.replace("'", "")
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
    print_synonyms(medias, "nlu_philharmonie_entities_medias")
