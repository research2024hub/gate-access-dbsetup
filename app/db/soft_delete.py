"""Soft-delete support for the ORM layer.

"Soft delete" = instead of really running ``DELETE FROM users WHERE id = 5``,
we set a timestamp column ``deleted_at`` on that row. The row physically stays
in the table forever; the application simply agrees to treat any row with a
non-NULL ``deleted_at`` as if it were gone.

Why bother? Because a real DELETE on ``users`` / ``account_holders`` cascades
(see the ON DELETE CASCADE foreign keys) and takes the person's events, guests,
faces, reports, etc. with it. Soft delete keeps all of that, still joined up and
still queryable.

This module has two parts:

1. ``SoftDeleteMixin`` -- a tiny reusable class. A model that "mixes it in"
   (``class User(SoftDeleteMixin, Base)``) automatically gets the ``deleted_at``
   column plus a couple of helper methods, with no copy-paste between models.

2. ``_filter_soft_deleted`` -- an *event hook*. SQLAlchemy lets you register a
   function that it calls automatically at a certain moment. We hook the moment
   "just before running any ORM query" and quietly append
   ``AND deleted_at IS NULL`` to every query that touches a soft-deletable
   table. That way individual queries scattered across the codebase don't each
   have to remember the filter -- forgetting it once would leak deleted rows.
"""
from __future__ import annotations

from sqlalchemy import Column, event, func
from app.db.types import UTCDateTime
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria


class SoftDeleteMixin:
    """Gives a model a ``deleted_at`` column and small helpers.

    A "mixin" is just a class you inherit *alongside* the real base class to
    share behaviour. ``class User(SoftDeleteMixin, Base): ...`` -- put the mixin
    first, then ``Base``.

    A plain ``Column`` defined on a mixin is copied onto each model that
    inherits it, so ``User`` and ``AccountHolder`` each end up with their own
    independent ``deleted_at`` column.
    """

    # NULL  -> the row is live
    # a timestamp -> the row was soft-deleted at that moment
    deleted_at = Column(UTCDateTime(), nullable=True)

    @property
    def is_deleted(self) -> bool:
        """``True`` if this row has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this row deleted. Add it to the session and commit afterwards,
        e.g. ``user.soft_delete(); session.commit()``.

        Uses the database clock (``func.now()``) so the value lines up with
        ``date_updated``, which is set by a database trigger.
        """
        self.deleted_at = func.now()

    def restore(self) -> None:
        """Undo a soft delete.

        The caller is responsible for first checking that the row's identity is
        free again -- e.g. that no *live* user has since taken this email/phone,
        and that the user has no other live account in the same estate.
        """
        self.deleted_at = None


# Pass this as ``execution_options`` to deliberately include soft-deleted rows,
# e.g. an admin "show deleted accounts" screen:
#
#     session.scalars(select(User), execution_options=INCLUDE_DELETED)
#
INCLUDE_DELETED = {"include_deleted": True}


@event.listens_for(Session, "do_orm_execute")
def _filter_soft_deleted(state: ORMExecuteState) -> None:
    """Called automatically by SQLAlchemy before it runs any ORM statement.

    ``state`` describes the statement about to run. We add our filter only when
    it makes sense:

    * ``state.is_select`` -- only SELECTs. We never touch INSERT/UPDATE/DELETE,
      so you can still write to (and soft-delete) these rows normally.
    * not ``is_column_load`` / ``is_relationship_load`` -- these are the extra
      little SELECTs SQLAlchemy fires to lazily fill in a relationship or a
      deferred column on rows it has *already* loaded. We leave those alone;
      filtering them causes surprising results. (Consequence: a *lazy*
      ``user.account_holders`` load is NOT filtered -- prefer eager loading
      (``selectinload``/``joinedload``), which IS covered, or filter that query
      yourself.)
    * ``include_deleted`` not set -- lets a caller opt out (see INCLUDE_DELETED).

    ``with_loader_criteria`` is the SQLAlchemy tool that does the real work: it
    injects a WHERE clause for *every* appearance of the target entity in the
    statement -- the main table and, with ``include_aliases=True``, any JOINed
    or eagerly-loaded copies of it too.
    """
    if not state.is_select:
        return
    if state.is_column_load or state.is_relationship_load:
        return
    if state.execution_options.get("include_deleted", False):
        return

    state.statement = state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,                       # -> applies to every subclass
            lambda cls: cls.deleted_at.is_(None),  # -> the criteria to add
            include_aliases=True,                  # -> also JOINs / eager loads
        )
    )
