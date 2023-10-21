from json import loads, dumps


def write_dict_to_json(file_path: str, data: dict):
    json_text = dumps(data, indent=2, ensure_ascii=False)

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(json_text)


def read_json_to_dict(file_path: str) -> dict:
    with open(file_path, "r") as file:
        text = file.read()

        data = loads(text)

    return data
