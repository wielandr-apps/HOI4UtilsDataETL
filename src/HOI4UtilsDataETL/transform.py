"""For transforming data from HOI4's internal data format into a more generalizable format"""
from typing import Union, Generator, TextIO, Any
import os

from utils import HOI4Directory


class HOI4DataParseError(ValueError):
    pass


def transform_hoi4_data_directory(dir_path: str) -> dict[str, list]:
    result = dict()
    for file_path in os.listdir(dir_path):
        file_name, file_ext = os.path.splitext(file_path)
        if file_ext == '.txt':
            result[file_name] = transform_hoi4_data_file(os.path.join(dir_path, file_path))
    return result


def transform_hoi4_data_file(file_path: str) -> Union[dict, list]:
    with open(file_path, 'r') as f:
        return transform_hoi4_data(f)


def transform_hoi4_data(data: TextIO) -> Union[list[str], dict[str, Any]]:
    """The main entry-point for all transforms"""
    tokens = hoi4_data_token_generator(data)
    return transform_hoi4_data_tokens(tokens)


def hoi4_data_token_generator(data: TextIO) -> Generator[str, int, str]:
    """Takes TextIO (e.g. a file) in hoi4 structured format and tokenizes the input for parsing"""
    for line_num, line in enumerate(data.readlines()):
        # Removes comments and splits the line into tokens
        tokens = line.strip().split('#')[0].strip().split()
        for token in tokens:
            if token != '':
                yield token, line_num, line


def transform_hoi4_data_tokens(tokens: Generator[str, int, str]) -> Union[list[str], dict[str, Any]]:
    """The workhorse for parsing hoi4 data inputs. Is pretty lenient with the format of the input file."""
    start = 0
    found_key = 1
    found_equals = 2

    state = start
    key = None
    result = dict()
    for token, line_num, line in tokens:
        if state == start:
            if token == '}':
                break
            elif token in ['=', '{']:
                raise HOI4DataParseError("Unexpected token '{}' while searching for key in line {}: {}"
                                         .format(token, line_num, line))
            key = token
            state = found_key

        elif state == found_key:
            if token == '{':
                result[key] = transform_hoi4_data_tokens(tokens)
                state = start
            elif token == '=':
                state = found_equals
            elif token == '}':
                result[key] = None
                break
            else:
                result[key] = None
                key = token

        else:
            # state == found_equals
            if token in ['=', '}']:
                raise HOI4DataParseError("Unexpected token '{}' while searching for value in line {}: {}"
                                         .format(token, line_num, line))
            elif token == '{':
                result[key] = transform_hoi4_data_tokens(tokens)
                state = start
            else:
                result[key] = parse_value(token)
                state = start

    if all(value is None for value in result.values()):
        result = [key for key in result.keys()]

    return result


def parse_value(value: str) -> Union[str, int, float]:
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def is_ship_subunit(unit_data: dict):
    print("")
    for sub_unit_data in unit_data["sub_units"].values():
        yield sub_unit_data.get("map_icon_category", None) == "ship"

def transform_hoi4_unit_data(directory: HOI4Directory) -> dict:
    unit_data = transform_hoi4_data_directory(directory.units())
    result = {
        "air": dict(),
        "land": dict(),
        "sea": dict()
    }

    for unit_key, unit_data in unit_data.items():
        if unit_key == "air":
            result[unit_key] = unit_data
        elif any(is_ship_subunit(unit_data)):
            if not all(is_ship_subunit(unit_data)):
                HOI4DataParseError("Some sub unit is not in a ship in a list of ships: {}".format(unit_data))
            result["sea"][unit_key] = unit_data
        else:
            result["land"][unit_key] = unit_data

    return result



if __name__ == "__main__":
    # Temporary test
    import json
    hoi4_dir = HOI4Directory('D:\\SteamLibrary\\steamapps\\common\\Hearts of Iron IV')
    # print(json.dumps(transform_hoi4_data_directory(hoi4_dir.units()), indent=2))
    print(json.dumps(transform_hoi4_unit_data(hoi4_dir), indent=2))
