import requests
import yaml


def download_parsed_yaml_file_content(url: str) -> dict:
    file_content_yaml = requests.get(url).content.decode("utf-8")
    file_content_dict = yaml.load(file_content_yaml)
    return file_content_dict
