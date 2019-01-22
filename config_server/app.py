import json
import os
import sys
from logging.config import dictConfig

from flask import Flask
from flask import jsonify, request
from flask_script import Manager, Server
from github import Github

from config_server.config import Config
from config_server.constants import BASE_CONFIGURATION_PATH
from config_server.logging_config import logging_config
from config_server.utils import download_parsed_yaml_file_content

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
if GITHUB_ACCESS_TOKEN is None:
    sys.exit(1)
GITHUB_CONFIG_REPO = os.getenv("GITHUB_CONFIG_REPO")
if GITHUB_CONFIG_REPO is None:
    sys.exit(1)

g = Github(GITHUB_ACCESS_TOKEN)
repo = g.get_user().get_repo(GITHUB_CONFIG_REPO)


class FlaskConfigServer(Server):
    def __call__(self, app, *args, **kwargs):
        load_all_configs()
        return Server.__call__(self, app, *args, **kwargs)


dictConfig(logging_config)

app = Flask(__name__)
manager = Manager(app)

manager.add_command("runserver", FlaskConfigServer())

app.config["config"] = Config()


def load_all_configs():
    tree = repo.get_git_tree("master").tree
    for element in tree:
        path = element.path
        config_path = path.split(".")[0]
        app.logger.info(f"Adding {config_path} to configs")
        download_url = repo.get_file_contents(path).download_url
        content = download_parsed_yaml_file_content(download_url)
        if element.path == BASE_CONFIGURATION_PATH:
            app.config["config"].update_base(content)
        else:
            app.config["config"][config_path] = content
    app.logger.info(f"Initial configuration: {app.config['config']}")


@app.route("/<config_name>")
def config_route(config_name):
    # TODO: think about favicon.ico
    try:
        config_data = app.config["config"][config_name]
    except KeyError:
        return jsonify({"message": "No such config on server"}), 404
    return jsonify(config_data)


@app.route("/", methods=["POST"])
def config_change_hook():
    data = json.loads(request.data.decode("utf-8"))
    commits = data["commits"]
    for commit in commits:
        added = commit["added"]
        for path in added:
            config_path = path.split(".")[0]
            app.logger.info(f"Added {config_path} configuration")
            download_url = repo.get_file_contents(path, ref=commit["id"]).download_url
            content = download_parsed_yaml_file_content(download_url)
            app.config["config"][config_path] = content
        removed = commit["removed"]
        for path in removed:
            config_path = path.split(".")[0]
            app.logger.info(f"Removed {config_path} configuration")
            app.config["config"].delete(config_path)
        modified = commit["modified"]
        for path in modified:
            config_path = path.split(".")[0]
            app.logger.info(f"Modified {config_path} configuration")
            download_url = repo.get_file_contents(path, ref=commit["id"]).download_url
            content = download_parsed_yaml_file_content(download_url)
            app.config["config"][config_path] = content
    app.logger.info(f"After push configuration: {app.config['config']}")
    return jsonify()


if __name__ == "__main__":
    manager.run()
