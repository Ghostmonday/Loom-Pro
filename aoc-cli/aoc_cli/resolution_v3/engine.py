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
        # CONTRACT: rule checks are dry reads. Stability calls this path and
        # therefore depends on every check_* function remaining side-effect free.
        return applicable_rule(self.cg, locus)

    def run(self, max_steps: int = 200) -> dict:
        self._seed_worklist()

        step = 0
        trace = []

        # FAULT BOUNDARY: even the initial potential calculation is untrusted.
        # A raw exception must become a deterministic ENGINE_FAULT payload.
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
                # B2 is a global fallback and may run only after the local
                # worklist drains; otherwise it can pre-empt local rule priority.
                elif not apply_b2(self.cg, self.worklist):
                    break

                step += 1
                psi_new = self.cg.psi()

                fault_detail = self._check_termination(step, psi_new, psi_previous)
                if fault_detail:
                    return self._report(EngineStatus.ENGINE_FAULT, step, trace, fault_detail=fault_detail)

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
        status = self._evaluate_status(valid, stable)

        fault_detail = None
        if status == EngineStatus.ENGINE_FAULT and step >= max_steps:
            fault_detail = f"step budget exhausted at {max_steps} before stability"

        return self._report(status, step, trace, valid=valid, stable=stable, fault_detail=fault_detail)

    def _seed_worklist(self) -> None:
        # DETERMINISM: seed the initial frontier canonically; never inherit dict
        # insertion order for nodes. Edge indices are the graph's stable handles.
        for node_id in sorted(self.cg.nodes):
            self.worklist.push(Locus.node(node_id), NORMAL)
        for index in range(len(self.cg.edges)):
            self.worklist.push(Locus.edge(index), NORMAL)

    def _check_termination(self, step: int, psi_new: tuple, psi_previous: tuple) -> str | None:
        # TERMINATION PROOF: every applied rewrite must strictly lower
        # the existing lexicographic Psi tuple. Do not weaken this check
        # or patch Psi automatically to accommodate a new rule.
        fault = self.injected_fault and step == 2
        if fault or not (psi_new < psi_previous):
            suffix = " [INJECTED]" if fault else ""
            return f"Psi did not strictly decrease: {psi_previous} -> {psi_new}{suffix}"
        return None

    def _evaluate_status(self, valid: bool, stable: bool) -> EngineStatus:
        # STATUS CONTRACT:
        # - CANONICAL: stable and valid.
        # - STUCK: stable but invalid/unresolved input.
        # - ENGINE_FAULT: instability or an internal contract failure.
        if valid and stable:
            return EngineStatus.CANONICAL
        if stable:
            return EngineStatus.STUCK
        return EngineStatus.ENGINE_FAULT

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
        # REPORTING MUST NOT MASK THE ORIGINAL FAILURE. Stability is best-effort
        # here because this method is also used from exception paths.
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
