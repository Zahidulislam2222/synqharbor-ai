"""Serialize acknowledged control changes with publication and external writes."""
from sqlalchemy import update
from sqlalchemy.orm import Session

from .models import Workspace


def lock_workspace(db: Session, workspace_id: str) -> None:
    # A no-op UPDATE holds a PostgreSQL row lock, and a SQLite writer lock, until
    # this transaction ends. Acquire before loading authorization or task rows.
    db.execute(update(Workspace).where(Workspace.id == workspace_id)
               .values(name=Workspace.name).execution_options(synchronize_session=False))
