"""Deterministic driver for the Loom constraint resolution engine v3."""

from __future__ import annotations

from aoc_cli.resolution_v3.model import EngineStatus, Locus
from aoc_cli.resolution_v3.reporting import report_payload
from aoc_cli.resolution_v3.rules import (
    applicable_rule,
    apply_a1,
    apply_a2_d1,
    apply_b1,
    apply_b2,
)
from aoc_cli.resolution_v3.worklist import NORMAL, Worklist


class Engine:
    """Deterministic propagation and resolution driver."""

    def __init__(self, cg, injected_fault: bool = False) -> None:
        self.cg = cg
        self.worklist = Worklist()
        self.injected_fault = injected_fault

    def applicable_rule(self, locus: Locus):
        return applicable_rule(self.cg, locus)

    def run(self, max_steps: int = 200) -> dict:
        for node_id in sorted(self.cg.nodes):
            self.worklist.push(Locus.node(node_id), NORMAL)
        for index in range(len(self.cg.edges)):
            self.worklist.push(Locus.edge(index), NORMAL)

        step = 0
        trace = []

        try:
            psi_previous = self.cg.psi()
            trace.append((0, psi_previous))
        except Exception as error:
            return self._report(
                EngineStatus.ENGINE_FAULT,
                step,
                trace,
                fault_detail=f"engine exception: {type(error).__name__}: {error}",
            )

        while step < max_steps:
            try:
                locus = self.worklist.pop()

                if locus is not None:
                    match = self.applicable_rule(locus)
                    if match is None:
                        continue
                    kind, payload = match
                    self._apply_local_rule(kind, payload)
                elif not apply_b2(self.cg, self.worklist):
                    break

                step += 1
                psi_new = self.cg.psi()

                fault = self.injected_fault and step == 2
                if fault or not (psi_new < psi_previous):
                    suffix = " [INJECTED]" if fault else ""
                    return self._report(
                        EngineStatus.ENGINE_FAULT,
                        step,
                        trace,
                        fault_detail=f"Psi did not strictly decrease: {psi_previous} -> {psi_new}{suffix}",
                    )

                trace.append((step, psi_new))
                psi_previous = psi_new

            except Exception as error:
                return self._report(
                    EngineStatus.ENGINE_FAULT,
                    step,
                    trace,
                    fault_detail=f"engine exception: {type(error).__name__}: {error}",
                )

        valid = self.cg.is_valid()
        stable = self.cg.is_stable(self)

        if valid and stable:
            status = EngineStatus.CANONICAL
        elif stable:
            status = EngineStatus.STUCK
        else:
            status = EngineStatus.ENGINE_FAULT

        fault_detail = None
        if status == EngineStatus.ENGINE_FAULT and step >= max_steps:
            fault_detail = f"step budget exhausted at {max_steps} before stability"

        return self._report(status, step, trace, valid=valid, stable=stable, fault_detail=fault_detail)

    def _apply_local_rule(self, kind: str, payload) -> None:
        if kind == "A1":
            apply_a1(self.cg, self.worklist, payload)
        elif kind == "A2_D1":
            apply_a2_d1(self.cg, self.worklist, payload)
        elif kind == "B1":
            apply_b1(self.cg, self.worklist, *payload)
        else:
            raise RuntimeError(f"unknown rule kind: {kind}")

    def _report(self, status, steps: int, trace, valid=None, stable=None, fault_detail: str | None = None) -> dict:
        if stable is None:
            try:
                stable = self.cg.is_stable(self)
            except Exception:
                stable = False
        return report_payload(
            self.cg,
            status,
            steps,
            trace,
            valid=valid,
            stable=stable,
            fault_detail=fault_detail,
        )


def resolve(cg, max_steps: int = 200, injected_fault: bool = False) -> dict:
    return Engine(cg, injected_fault=injected_fault).run(max_steps=max_steps)
