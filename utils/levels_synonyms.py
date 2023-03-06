from collections import defaultdict

level_sentences = {
    "cycle-1": [
        "faciles à jouer",
        "facile à jouer",
        "débutant",
        "accessibles aux débutants",
        "accessible à un débutant",
        "pour les débutants",
        "pour enfants",
        "pour les enfants",
        "de petit niveau",
        "de petits niveaux",
        "débutants",
        "pour apprendre le ",
        "pour petit niveau",
        "pour petits niveaux",
        "pour débuter en ",
        "pour débuter ",
        "pour s'initier à ",
        "élèves inscrits en ",
    ],
    "cycle-2": [
        "accessibles aux confirmés",
        "accessible au confirmé",
        "destinés aux musiciens confirmés",
        "destiné à un musicien confirmé",
        "destinés aux musiciens de niveau intermédiaire en ",
        "destiné à un musicien de niveau intermédiaire en ",
        "pour les confirmés",
        "pour un confirmé",
        "pour les intermédiaires",
        "pour un intermédiaire",
        "confirmés",
        "confirmé",
        "intermédiaires",
        "intermédiaire",
        "pour élèves de niveau confirmé en ",
        "pour un élève de niveaux confirmé en ",
        "pour se perfectionner en ",
        "pour continuer le ",
    ],
    "cycle-3": [
        "de niveau expert",
        "de niveaux experts",
        "expert",
        "experts",
        "destinés aux musiciens chevronnés",
        "destiné à un musicien chevronné",
        "destinés aux musiciens experts en ",
        "destiné à un musicien expert en ",
        "pour les musiciens très expérimentés dans la pratique du ",
        "pour un musicien très expérimenté dans la pratique du ",
        "pour élèves de niveau expert en ",
        "pour les très bons joueurs de ",
        "pour un très bon joueur de ",
    ],
}

level_worded = {
    "cycle-1": [
        "en 1er cycle",
        "1er cycle",
        "en 1e cycle",
        "de premier cycle",
        "premier cycle",
        "de 1e année",
        "1e année",
        "en 1ère année",
        "de première année",
        "en 2e année",
        "2e année",
        "2ème année",
        "de deuxième année",
        "deuxième année",
        "qui sont en 3e année",
        "qui est en 3e année",
        "élèves en 3ème année",
        "élève en 3ème année",
        "troisième année",
        "4e année",
        "de 4ème année",
    ],
    "cycle-2": [
        "en 2nd cycle",
        "en 2e cycle",
        "en 2eme cycle",
        "de second cycle",
        "de 5e année",
        "en 5ème année",
        "de cinquième année" "en 6e année",
        "6ème année",
        "de sixième année",
        "qui sont en 7e année",
        "qui est en 7e année",
        "élèves en 7ème année",
        "élève en 7ème année",
        "septième année",
    ],
    "cycle-3": [
        "en 3e cycle",
        "en 3eme cycle",
        "de troisième cycle",
        "de 8e année",
        "en 8ème année",
        "de huitième année" "en 9e année",
        "9ème année",
        "de neuvième année",
        "qui sont en 10e année",
        "qui est en 10e année",
        "élèves en 10ème année",
        "élève en 10ème année",
        "dixième année",
    ],
}

level_timing = {
    "cycle-1": [
        "1 an",
        "un an",
        "2 ans",
        "deux ans",
        "3 ans",
        "trois ans",
        "4 ans",
        "quatre ans",
    ],
    "cycle-2": [
        "5 ans",
        "5 ans",
        "6 ans",
        "six ans",
        "7 ans",
        "sept ans",
    ],
    "cycle-3": [
        "8 ans",
        "huit ans",
        "9 ans",
        "neuf ans",
        "10 ans",
        "dix ans",
    ],
}

all_levels = defaultdict(list)
for d in [level_sentences, level_timing, level_worded]:
    for k, v in d.items():  # use d.iteritems() in python 2
        for i in v:
            all_levels[k].append(i)
