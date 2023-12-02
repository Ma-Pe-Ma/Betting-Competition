import json

from collections import namedtuple

configuration_file_path : str = './configuration.json'

configuration = None

def convert_to_namedtuple(tuple_name : str, dictionary : dict) -> namedtuple:
    for key, value in dictionary.items():
            if isinstance(value, dict):
                dictionary[key] = convert_to_namedtuple(key, value) 
    return namedtuple(tuple_name, dictionary.keys())(**dictionary)

def load_configuration() -> namedtuple:
    with open(configuration_file_path) as config_file:
        configuration_dict = json.load(config_file)
        global configuration        
        configuration = convert_to_namedtuple('Configuration', configuration_dict)
        return configuration
    