"""Factory for the flask app."""

import logging

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from geneweaver.aon import __version__
from geneweaver.aon.controller.flask.controller import NS as AGR
from geneweaver.aon.controller.flask.healthcheck import NS as HEALTH_CHECK
from geneweaver.aon.core.config import config
from geneweaver.aon.core.database import SessionLocal
from sqlalchemy.orm import scoped_session


def create_app(app=None):
    """Create an instance of a flask app
    :param app: existing app if initialized
    :return:
    """
    app = app or Flask(__name__, static_url_path="/static", static_folder="static")

    app.config.from_object(config)

    app.app_context().push()

    logging.basicConfig(level=app.config["LOG_LEVEL"])

    api = Api(
        title=app.config["TITLE"],
        version=__version__,
        description=app.config["DESCRIPTION"],
    )

    # Add our service and healthcheck endpoints
    api.add_namespace(HEALTH_CHECK)
    api.add_namespace(AGR)

    api.init_app(app)

    with app.app_context():
        CORS(app)

    app.session = scoped_session(SessionLocal)

    @app.teardown_request(Exception)
    def close_session():
        app.session.close()
        return {"message": "END"}

    return app
