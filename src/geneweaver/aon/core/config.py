"""
Application config that uses environs module to load values from .env file or environment variables
"""

import logging
from environs import Env
from pydantic import BaseSettings


logger = logging.getLogger(__name__)

env = Env()
env.read_env()


class Config:
    TITLE = "Geneweaver Ortholog Normalizer"
    DESCRIPTION = "An application to aid in normalizing homology data."

    DEBUG = env.bool("DEBUG", default=False)
    TESTING = env.bool("TESTING", default=False)
    LOG_LEVEL = env.str("LOG_LEVEL", default="WARNING")

    # TODO - update to point to relevant databases
    DATABASE_URL_AGR = "postgresql+psycopg://localhost:5432/agr"
    DATABASE_URL_GW = "postgresql+psycopg://localhost:2222/geneweaver"