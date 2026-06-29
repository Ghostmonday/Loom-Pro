"""Loom Pipeline Coordinator — optional orchestration after handoff.

C11 (LOOM-204): After ``accept_handoff``, optionally collect teleology
receipts before synthesis. This module documents the call sequence and
provides a thin function so service / UI consumers have a single entry
point rather than manually ordering forge + teleology + synthesis steps.
"""

from __future__ import annotations

from typing import Any


def pipeline_handoff_with_teleology(
    driver: Any,
    intent: str,
    *,
    collect_teleology: bool = True,
) -> dict[str, Any]:
    """Accept a handed-off forge session, optionally collect teleology, and return state.

    Parameters
    ----------
    driver : UiIntentDriver
        The active UiIntentDriver instance with an already-confirmed forge
        session (handoff.confirm must have been called).
    intent : str
        The original user intent — forwarded to ``collect_teleology_receipt``.
    collect_teleology : bool
        When True (default), invoke teleology receipt collection immediately
        after the handoff is accepted.

    Returns
    -------
    dict
        Keys:
          - ``accept``: response from ``handoff.accept``
          - ``teleology``: teleology receipt dict (empty dict when
            ``collect_teleology=False``)

    Call sequence
    -------------
    The intended ordering when teleology is enabled::

        confirm_handoff → accept_handoff → collect_teleology_receipt → synthesize

    Service hooks that want teleology before synthesis can call this function
    instead of manually sequencing the three driver calls.
    """
    accept_data = driver.dispatch_loom_forge_action("handoff.accept")
    teleology_data: dict[str, Any] = {}

    if collect_teleology:
        teleology_data = driver.collect_teleology_receipt(intent)

    return {
        "accept": accept_data,
        "teleology": teleology_data,
    }
