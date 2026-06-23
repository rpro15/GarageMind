from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.domain.catalog import ClickEvent


class AffiliateLinkBuilder:
    """Builds affiliate URLs for partner products.

    The actual URL construction is delegated to the ``Partner`` model via
    :meth:`~app.domain.catalog.Partner.build_url`.  This class exists as a
    named service boundary so the URL logic can be replaced (e.g. with signed
    short-links) without touching route handlers.
    """

    def build(self, partner_url_template: str | None, product_id: str) -> str | None:
        if partner_url_template is None:
            return None
        return partner_url_template.format(product_id=product_id)


class ClickTrackingService:
    """Records and exposes click events for affiliate attribution.

    Uses an in-memory list suitable for development and testing.  A persistent
    adapter (e.g. SQLite, Redis) can be swapped in by replacing the store.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._events: list[ClickEvent] = []
        self._logger = logger or logging.getLogger(__name__)

    def record(
        self,
        product_id: str,
        partner_id: str,
        session_id: str | None = None,
    ) -> ClickEvent:
        event = ClickEvent(
            product_id=product_id,
            partner_id=partner_id,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            session_id=session_id,
        )
        self._events.append(event)
        self._logger.info(
            "click recorded product_id=%s partner_id=%s session_id=%s",
            product_id,
            partner_id,
            session_id,
        )
        return event

    def all_events(self) -> list[ClickEvent]:
        return list(self._events)

    def events_for_product(self, product_id: str) -> list[ClickEvent]:
        return [e for e in self._events if e.product_id == product_id]

    def events_for_partner(self, partner_id: str) -> list[ClickEvent]:
        return [e for e in self._events if e.partner_id == partner_id]
