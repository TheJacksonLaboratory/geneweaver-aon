"""Utilities for getting and setting up schema version db connections."""

import logging
from typing import List, Optional, Tuple

from geneweaver.aon.core.config import config
from geneweaver.aon.core.database import BaseAGR, BaseGW
from geneweaver.aon.models import Version
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger("uvicorn.error")


def get_latest_schema_version() -> Optional[Version]:
    """Get the latest schema version."""
    engine = create_engine(config.DB.URI)
    session = Session(bind=engine)
    version = (
        session.query(Version)
        .filter(Version.load_complete == True)  # noqa: E712
        .order_by(Version.id.desc())
        .first()
    )
    session.close()
    return version


def get_schema_versions() -> List[Version]:
    """Get all schema versions."""
    engine = create_engine(config.DB.URI)
    session = Session(bind=engine)
    versions = (
        session.query(Version)
        .filter(Version.load_complete == True)  # noqa: E712
        .order_by(Version.id.desc())
        .all()
    )
    session.close()
    return versions


def get_schema_version(version_id: int) -> Optional[Version]:
    """Get a schema version by ID."""
    engine = create_engine(config.DB.URI)
    session = Session(bind=engine)
    version = session.query(Version).get(version_id)
    session.close()
    return version


def mark_schema_version_load_complete(version_id: int) -> None:
    """Mark a schema version as loaded."""
    engine = create_engine(config.DB.URI)
    session = Session(bind=engine)
    version = session.query(Version).get(version_id)
    version.load_complete = True
    session.add(version)
    session.commit()
    session.close()


def set_up_sessionmanager(
    version: Optional[Version],
) -> Tuple[sessionmaker, Tuple[Engine, Engine]]:
    """Set up the session manager.

    :param version: The schema version to use.
    :return: The session manager.
    """
    gw_engine = create_engine(config.GW_DB.URI)
    if version is not None:
        engine = create_engine(config.DB.URI).execution_options(
            schema_translate_map={None: version.schema_name}
        )
    else:
        engine = create_engine(config.DB.URI)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session.configure(binds={BaseAGR: engine, BaseGW: gw_engine})
    return session, (engine, gw_engine)


def set_up_sessionmanager_by_schema(
    schema_versions: list[Version],
) -> dict[str, sessionmaker]:
    """Set up the session manager by schema version.

    :param schema_versions: The schema versions to use.
    :return: The session manager by schema version.
    """
    session_managers = {}
    engines = {}
    if len(schema_versions) == 0:
        schema_versions.append(None)
    for version in schema_versions:
        version_id = None if version is None else version.id
        logger.info(f"Setting up session manager for schema version {version_id}.")
        session_managers[version_id], engines[version_id] = set_up_sessionmanager(
            version
        )
    return session_managers, engines
