import json


def save_notes(notes):

    with open(
        "memory/notes.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            notes,
            file,
            indent=4
        )


def load_notes():

    try:

        with open(
            "memory/notes.json",
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except:

        return []