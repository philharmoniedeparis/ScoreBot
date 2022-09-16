from collections import defaultdict

level_sentences = {
    "cycle-1": [
        "accessibles aux débutants",
        "pour les débutants",
        "débutants",
        "débutant",
        "pour apprendre le ",
        "pour petit niveau",
        "pour débuter en ",
        "pour débuter ",
        "pour s'initier à ",
        "élèves inscrits en ",
    ],
    "cycle-2": [
        "accessibles aux confirmés",
        "destinés aux musiciens confirmés",
        "destinés aux musiciens de niveau intermédiaire en ",
        "pour les confirmés",
        "pour les intermédiaires",
        "confirmés",
        "confirmé",
        "intermédiaires",
        "intermédiaire",
        "pour élèves de niveau confirmé en ",
        "pour se perfectionner en ",
        "pour continuer le ",
    ],
    "cycle-3": [
        "de niveau expert",
        "expert",
        "experts",
        "destinés aux musiciens chevronnés",
        "destinés aux musiciens experts en ",
        "pour les musiciens très expérimentés dans la pratique du ",
        "pour élèves de niveau expert en ",
        "pour les très bons joueurs de ",
    ]
}

level_worded = {
    "cycle-1": [
        "débutants",
        "débutant",
        "en 1er cycle",
        "de premier cycle",
        "de 1e année",
        "en 1ère année",
        "de première année"
        "en 2e année",
        "2ème année",
        "de deuxième année",
        "qui sont en 3e année",
        "élèves en 3ème année",
        "troisième année",
        "4e année",
        "de 4ème année",
    ],
    "cycle-2": [
        "confirmés",
        "confirmé",
        "intermédiaires",
        "intermédiaire",
        "en 2nd cycle",
        "de second cycle",
        "de 5e année",
        "en 5ème année",
        "de cinquième année"
        "en 6e année",
        "6ème année",
        "de sixième année",
        "qui sont en 7e année",
        "élèves en 7ème année",
        "septième année",
    ],
    "cycle-3": [
        "expert",
        "experts",
        "en 3e cycle",
        "de troisième cycle",
        "de 8e année",
        "en 8ème année",
        "de huitième année"
        "en 9e année",
        "9ème année",
        "de neuvième année",
        "qui sont en 10e année",
        "élèves en 10ème année",
        "dixième année",
    ]
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
    ]
}

all_levels = defaultdict(list)
for d in [level_sentences, level_timing, level_worded]:
    for k, v in d.items():  # use d.iteritems() in python 2
        for i in v:
            all_levels[k].append(i)