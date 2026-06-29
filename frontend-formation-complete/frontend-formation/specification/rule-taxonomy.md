# Frontend-Formation Rule Taxonomy

Version: `1.0.0`

All enforced diagnostics are hard `ERROR`s. Reserved rules document limits that require intent review or runtime/controller instrumentation.

## R001 — Contract Anchoring

`FFM-R001-01` unclassified semantic interactive element  
`FFM-R001-02` action control missing action ID  
`FFM-R001-03` action ID absent from registry  
`FFM-R001-04` display missing contract path  
`FFM-R001-05` presentation node leaks semantic bindings  
`FFM-R001-06` inline event handler  
`FFM-R001-07` action/display node missing stable ID

## R002 — Screen Mission Singularity

`FFM-R002-01` manifest mission missing  
`FFM-R002-02` DOM mission declaration missing  
`FFM-R002-03` reserved: competing workflows require intent-level review  
`FFM-R002-04` screen identity mismatch  
`FFM-R002-05` multiple screen roots  
`FFM-R002-06` mission identity mismatch

## R003 — Strict Element Mapping

`FFM-R003-01` invalid classification  
`FFM-R003-02` classified DOM node absent from manifest  
`FFM-R003-03` classification mismatch  
`FFM-R003-04` reserved: runtime classification mutation  
`FFM-R003-05` manifest node absent from DOM  
`FFM-R003-06` action binding mismatch  
`FFM-R003-07` contract-path mismatch  
`FFM-R003-08` feedback-target mismatch  
`FFM-R003-09` duplicate DOM ID  
`FFM-R003-10` duplicate manifest ID

## R004 — Guaranteed Feedback Loop

`FFM-R004-01` action control missing feedback target  
`FFM-R004-02` feedback target absent from DOM  
`FFM-R004-03` action lacks one or more canonical lifecycle states  
`FFM-R004-04` reserved: controller projection requires JS/runtime analysis  
`FFM-R004-05` feedback target absent from manifest or not display-classified there  
`FFM-R004-06` feedback target not display-classified in DOM

## R005 — Five-Domain Knowledge Binding

`FFM-R005-01` missing domain binding  
`FFM-R005-02` unresolved knowledge binding  
`FFM-R005-03` registry domain mismatch  
`FFM-R005-04` malformed not-applicable declaration

## R006 — Accessibility-Safe Defaults

`FFM-R006-01` positive tabindex  
`FFM-R006-02` redundant native ARIA role  
`FFM-R006-03` action control missing accessible name  
`FFM-R006-04` custom action control missing interactive role  
`FFM-R006-05` custom action control missing tabindex=0  
`FFM-R006-06` feedback target lacks live-region semantics

## R007 — Continuous Smoke Verification

`FFM-R007-01` no smoke scenario  
`FFM-R007-02` missing required scenario step kind  
`FFM-R007-03` scenario screen mismatch  
`FFM-R007-04` unknown element target  
`FFM-R007-05` interaction target is not an action control  
`FFM-R007-06` unknown contract projection path  
`FFM-R007-07` duplicate scenario ID
