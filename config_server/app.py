import json
import os
import sys
from logging.config import dictConfig

from flask import Flask
from flask import jsonify, request
from flask_script import Manager, Server
from github import Github

from config_server.logging_config import logging_config
from config_server.utils import download_parsed_yaml_file_content

GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
if GITHUB_ACCESS_TOKEN is None:
    sys.exit(1)
CONFIG_REPO = os.getenv("CONFIG_REPO")
if CONFIG_REPO is None:
    sys.exit(1)

g = Github(GITHUB_ACCESS_TOKEN)
repo = g.get_user().get_repo(CONFIG_REPO)


class FlaskConfigServer(Server):
    def __call__(self, app, *args, **kwargs):
        load_all_configs()
        return Server.__call__(self, app, *args, **kwargs)


dictConfig(logging_config)

app = Flask(__name__)
manager = Manager(app)

manager.add_command("runserver", FlaskConfigServer())

app.config["configs"] = {}


def load_all_configs():
    tree = repo.get_git_tree("master").tree
    for element in tree:
        app.logger.info(f"Adding {element.path} to configs")
        download_url = repo.get_file_contents(element.path).download_url
        content = download_parsed_yaml_file_content(download_url)
        app.config["configs"][element.path] = content
    app.logger.info(f"Initial configuration: {app.config['configs']}")


@app.route("/<config_name>")
def config_route(config_name):
    config_data = app.config["configs"].get(config_name)
    if config_data is None:
        return jsonify({"message": "No such config on server"}), 404
    return jsonify(config_data)


@app.route("/", methods=["POST"])
def config_change_hook():
    data = json.loads(request.data.decode("utf-8"))
    commits = data["commits"]
    for commit in commits:
        added = commit["added"]
        for path in added:
            app.logger.info(f"Added {path} configuration")
            download_url = repo.get_file_contents(path, ref=commit["id"]).download_url
            content = download_parsed_yaml_file_content(download_url)
            app.config["configs"][path] = content
        removed = commit["removed"]
        for path in removed:
            app.logger.info(f"Removed {path} configuration")
            del app.config["configs"][path]
        modified = commit["modified"]
        for path in modified:
            app.logger.info(f"Modified {path} configuration")
            download_url = repo.get_file_contents(path, ref=commit["id"]).download_url
            content = download_parsed_yaml_file_content(download_url)
            app.config["configs"][path] = content
    app.logger.info(f"After push configuration: {app.config['configs']}")
    return jsonify()


if __name__ == "__main__":
    manager.run()
