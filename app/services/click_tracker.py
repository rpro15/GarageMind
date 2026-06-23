from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.domain.models import ClickEvent


class ClickTrackingService:
    """Records outbound affiliate click events.

    In the MVP events are stored in-memory.  A future iteration can persist
    them to the database without changing the service interface.
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._events: list[ClickEvent] = []

    def record(
        self,
        product_id: str,
        partner_id: str,
        affiliate_url: str,
    ) -> ClickEvent:
        event = ClickEvent(
            product_id=product_id,
            partner_id=partner_id,
            affiliate_url=affiliate_url,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._events.append(event)
        self._logger.info(
            "Click recorded: product=%s partner=%s url=%s",
            product_id,
            partner_id,
            affiliate_url,
        )
        return event

    def list_events(self) -> list[ClickEvent]:
        return list(self._events)
