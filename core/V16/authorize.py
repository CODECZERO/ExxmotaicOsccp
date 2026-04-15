"""core.V16.authorize — Authorize handler (OCPP 1.6J)."""

from __future__ import annotations

import logging

from ocpp.v16 import call_result
from ocpp.v16.enums import AuthorizationStatus

logger = logging.getLogger(__name__)


def handle_authorize(id_tag: str, **kwargs) -> call_result.Authorize:
    """Accept any id_tag (echo / debug mode)."""
    logger.info("Authorize  id_tag=%s  extras=%s", id_tag, kwargs)
    return call_result.Authorize(
        id_tag_info={"status": AuthorizationStatus.accepted},
    )
