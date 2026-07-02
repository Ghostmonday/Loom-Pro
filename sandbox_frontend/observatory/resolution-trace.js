window.LOOM_TRACE = {
 "meta": {
  "generated": "2026-07-02T05:43:49+00:00",
  "engine": "aoc_cli.resolution_v3 (real run, no mocks)",
  "fixture": "ingest/billing/retry demo \u2014 A1 x2, B1, B2 weld, STUCK, A3 boundary",
  "doctrine": "the model proposes, the engine decides",
  "replay_digest": "0e164d933deaddfa"
 },
 "resolution": {
  "steps": [
   {
    "step": 0,
    "psi": [
     2,
     0,
     4,
     1
    ],
    "log": [],
    "snapshot": {
     "nodes": [
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "queue_mgr",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "retry_daemon",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "queue_mgr",
       "modality": "REQ",
       "label": "calls",
       "active": true
      },
      {
       "u": "queue_mgr",
       "v": "retry_daemon",
       "modality": "REQ",
       "label": "calls_back",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    }
   },
   {
    "step": 1,
    "psi": [
     2,
     0,
     4,
     0
    ],
    "log": [
     "[B1] clash on ingest_api->billing_core 'calls' REQ vs FORBID; priority rule 5: FORBID wins -> REQ edge deactivated"
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "queue_mgr",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "retry_daemon",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "queue_mgr",
       "modality": "REQ",
       "label": "calls",
       "active": true
      },
      {
       "u": "queue_mgr",
       "v": "retry_daemon",
       "modality": "REQ",
       "label": "calls_back",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    }
   },
   {
    "step": 2,
    "psi": [
     1,
     1,
     4,
     0
    ],
    "log": [
     "[A1] introduced latent node 'audit_buffer' (required by billing_core -[flushes_to]-> audit_buffer); intersected domain=['log_sink', 'service']"
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "audit_buffer",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "queue_mgr",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "retry_daemon",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "queue_mgr",
       "modality": "REQ",
       "label": "calls",
       "active": true
      },
      {
       "u": "queue_mgr",
       "v": "retry_daemon",
       "modality": "REQ",
       "label": "calls_back",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    }
   },
   {
    "step": 3,
    "psi": [
     0,
     2,
     4,
     0
    ],
    "log": [
     "[A1] introduced latent node 'metrics_hub' (required by ingest_api -[emits_to]-> metrics_hub); undeclared labels=['emits_to']"
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "audit_buffer",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "metrics_hub",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "queue_mgr",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "retry_daemon",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "queue_mgr",
       "modality": "REQ",
       "label": "calls",
       "active": true
      },
      {
       "u": "queue_mgr",
       "v": "retry_daemon",
       "modality": "REQ",
       "label": "calls_back",
       "active": true
      },
      {
       "u": "retry_daemon",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    }
   },
   {
    "step": 4,
    "psi": [
     0,
     2,
     0,
     0
    ],
    "log": [
     "[B2] welded SCC ['queue_mgr', 'retry_daemon'] (size=2) into 'WELD[queue_mgr|retry_daemon]'"
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "WELD[queue_mgr|retry_daemon]",
       "status": "KNOWN",
       "type": "composite",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "audit_buffer",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "metrics_hub",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls_back",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    }
   }
  ],
  "status": "STUCK",
  "errors": [
   "latent nodes or partial edges remain unresolved"
  ]
 },
 "proposals": {
  "firings": [
   {
    "firing": 1,
    "evaluations": [
     {
      "proposal": {
       "proposal_id": "P-004",
       "kind": "DECLARE_LABEL_DOMAIN_AND_RESOLVE_TARGET",
       "target_id": "metrics_hub",
       "selected_type": "log_sink",
       "label": "emits_to",
       "label_domain": [
        "log_sink"
       ],
       "scope": [
        "NODE:metrics_hub"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'metrics_hub'"
       },
       {
        "name": "target exists and is latent",
        "pass": true,
        "detail": "'metrics_hub' is LATENT_UNRESOLVED"
       },
       {
        "name": "kind-specific legality",
        "pass": true,
        "detail": "new label 'emits_to' -> ['log_sink']"
       },
       {
        "name": "no new validation errors",
        "pass": true,
        "detail": "errors 2 -> 1, no new classes"
       },
       {
        "name": "psi strictly decreases",
        "pass": true,
        "detail": "Psi (0, 2, 0, 0) -> (0, 1, 0, 0)"
       }
      ],
      "decision": {
       "proposal_id": "P-004",
       "status": "ACCEPTED",
       "reason": "accepted: Psi (0, 2, 0, 0) -> (0, 1, 0, 0)",
       "psi_before": [
        0,
        2,
        0,
        0
       ],
       "psi_after": [
        0,
        1,
        0,
        0
       ]
      }
     },
     {
      "proposal": {
       "proposal_id": "P-001",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": "log_sink",
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'audit_buffer'"
       },
       {
        "name": "target exists and is latent",
        "pass": true,
        "detail": "'audit_buffer' is LATENT_UNRESOLVED"
       },
       {
        "name": "kind-specific legality",
        "pass": true,
        "detail": "'log_sink' is in aggregated domain ['log_sink', 'service']"
       },
       {
        "name": "no new validation errors",
        "pass": true,
        "detail": "errors 2 -> 2, no new classes"
       },
       {
        "name": "psi strictly decreases",
        "pass": true,
        "detail": "Psi (0, 2, 0, 0) -> (0, 1, 0, 0)"
       }
      ],
      "decision": {
       "proposal_id": "P-001",
       "status": "REJECTED",
       "reason": "superseded: deterministic selection chose 'P-004' this firing",
       "psi_before": [
        0,
        2,
        0,
        0
       ],
       "psi_after": [
        0,
        1,
        0,
        0
       ]
      }
     },
     {
      "proposal": {
       "proposal_id": "P-002",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": "database",
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'audit_buffer'"
       },
       {
        "name": "target exists and is latent",
        "pass": true,
        "detail": "'audit_buffer' is LATENT_UNRESOLVED"
       },
       {
        "name": "kind-specific legality",
        "pass": false,
        "detail": "domain membership failed"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-002",
       "status": "REJECTED",
       "reason": "selected type 'database' outside aggregated domain ['log_sink', 'service']",
       "psi_before": [
        0,
        2,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-005",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": null,
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": false,
        "detail": "selected_type is None"
       },
       {
        "name": "authority: declared scope",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-005",
       "status": "REJECTED",
       "reason": "malformed proposal: selected_type is required for RESOLVE_LATENT_TYPE",
       "psi_before": [
        0,
        2,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-003",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "metrics_hub",
       "selected_type": "service",
       "label": null,
       "label_domain": [],
       "scope": [],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": false,
        "detail": "target locus missing from declared scope"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-003",
       "status": "REJECTED",
       "reason": "authority violation: scope does not include node 'metrics_hub'",
       "psi_before": [
        0,
        2,
        0,
        0
       ],
       "psi_after": null
      }
     }
    ],
    "selected": "P-004",
    "psi": [
     0,
     1,
     0,
     0
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "WELD[queue_mgr|retry_daemon]",
       "status": "KNOWN",
       "type": "composite",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "audit_buffer",
       "status": "LATENT_UNRESOLVED",
       "type": null,
       "layer": null,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "metrics_hub",
       "status": "KNOWN",
       "type": "log_sink",
       "layer": 1,
       "domain": [
        "log_sink"
       ],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls_back",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    },
    "log": [
     "[A3] llm proposal 'P-004' resolved 'metrics_hub' as type=log_sink (source=llm; engine-accepted)"
    ]
   },
   {
    "firing": 2,
    "evaluations": [
     {
      "proposal": {
       "proposal_id": "P-001",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": "log_sink",
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'audit_buffer'"
       },
       {
        "name": "target exists and is latent",
        "pass": true,
        "detail": "'audit_buffer' is LATENT_UNRESOLVED"
       },
       {
        "name": "kind-specific legality",
        "pass": true,
        "detail": "'log_sink' is in aggregated domain ['log_sink', 'service']"
       },
       {
        "name": "no new validation errors",
        "pass": true,
        "detail": "errors 1 -> 0, no new classes"
       },
       {
        "name": "psi strictly decreases",
        "pass": true,
        "detail": "Psi (0, 1, 0, 0) -> (0, 0, 0, 0)"
       }
      ],
      "decision": {
       "proposal_id": "P-001",
       "status": "ACCEPTED",
       "reason": "accepted: Psi (0, 1, 0, 0) -> (0, 0, 0, 0)",
       "psi_before": [
        0,
        1,
        0,
        0
       ],
       "psi_after": [
        0,
        0,
        0,
        0
       ]
      }
     },
     {
      "proposal": {
       "proposal_id": "P-002",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": "database",
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'audit_buffer'"
       },
       {
        "name": "target exists and is latent",
        "pass": true,
        "detail": "'audit_buffer' is LATENT_UNRESOLVED"
       },
       {
        "name": "kind-specific legality",
        "pass": false,
        "detail": "domain membership failed"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-002",
       "status": "REJECTED",
       "reason": "selected type 'database' outside aggregated domain ['log_sink', 'service']",
       "psi_before": [
        0,
        1,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-005",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": null,
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": false,
        "detail": "selected_type is None"
       },
       {
        "name": "authority: declared scope",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-005",
       "status": "REJECTED",
       "reason": "malformed proposal: selected_type is required for RESOLVE_LATENT_TYPE",
       "psi_before": [
        0,
        1,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-003",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "metrics_hub",
       "selected_type": "service",
       "label": null,
       "label_domain": [],
       "scope": [],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": false,
        "detail": "target locus missing from declared scope"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-003",
       "status": "REJECTED",
       "reason": "authority violation: scope does not include node 'metrics_hub'",
       "psi_before": [
        0,
        1,
        0,
        0
       ],
       "psi_after": null
      }
     }
    ],
    "selected": "P-001",
    "psi": [
     0,
     0,
     0,
     0
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "WELD[queue_mgr|retry_daemon]",
       "status": "KNOWN",
       "type": "composite",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "audit_buffer",
       "status": "KNOWN",
       "type": "log_sink",
       "layer": 1,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "metrics_hub",
       "status": "KNOWN",
       "type": "log_sink",
       "layer": 1,
       "domain": [
        "log_sink"
       ],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls_back",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    },
    "log": [
     "[A3] llm proposal 'P-001' resolved 'audit_buffer' as type=log_sink (source=llm; engine-accepted)"
    ]
   },
   {
    "firing": 3,
    "evaluations": [
     {
      "proposal": {
       "proposal_id": "P-002",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": "database",
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": true,
        "detail": "scope covers node 'audit_buffer'"
       },
       {
        "name": "target exists and is latent",
        "pass": false,
        "detail": "status=KNOWN"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-002",
       "status": "REJECTED",
       "reason": "target 'audit_buffer' is not latent",
       "psi_before": [
        0,
        0,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-005",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "audit_buffer",
       "selected_type": null,
       "label": null,
       "label_domain": [],
       "scope": [
        "NODE:audit_buffer"
       ],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": false,
        "detail": "selected_type is None"
       },
       {
        "name": "authority: declared scope",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-005",
       "status": "REJECTED",
       "reason": "malformed proposal: selected_type is required for RESOLVE_LATENT_TYPE",
       "psi_before": [
        0,
        0,
        0,
        0
       ],
       "psi_after": null
      }
     },
     {
      "proposal": {
       "proposal_id": "P-003",
       "kind": "RESOLVE_LATENT_TYPE",
       "target_id": "metrics_hub",
       "selected_type": "service",
       "label": null,
       "label_domain": [],
       "scope": [],
       "source": "llm"
      },
      "checks": [
       {
        "name": "well-formed payload",
        "pass": true,
        "detail": "frozen dataclass constructed; ids validated at boundary"
       },
       {
        "name": "kind completeness",
        "pass": true,
        "detail": "kind-specific required fields present"
       },
       {
        "name": "authority: declared scope",
        "pass": false,
        "detail": "target locus missing from declared scope"
       },
       {
        "name": "target exists and is latent",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "kind-specific legality",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "no new validation errors",
        "pass": null,
        "detail": "not reached"
       },
       {
        "name": "psi strictly decreases",
        "pass": null,
        "detail": "not reached"
       }
      ],
      "decision": {
       "proposal_id": "P-003",
       "status": "REJECTED",
       "reason": "authority violation: scope does not include node 'metrics_hub'",
       "psi_before": [
        0,
        0,
        0,
        0
       ],
       "psi_after": null
      }
     }
    ],
    "selected": null,
    "psi": [
     0,
     0,
     0,
     0
    ],
    "snapshot": {
     "nodes": [
      {
       "id": "WELD[queue_mgr|retry_daemon]",
       "status": "KNOWN",
       "type": "composite",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "audit_buffer",
       "status": "KNOWN",
       "type": "log_sink",
       "layer": 1,
       "domain": [
        "log_sink",
        "service"
       ],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "billing_core",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": false,
       "sink_permitted": false
      },
      {
       "id": "ingest_api",
       "status": "KNOWN",
       "type": "service",
       "layer": 1,
       "domain": [],
       "root_permitted": true,
       "sink_permitted": false
      },
      {
       "id": "metrics_hub",
       "status": "KNOWN",
       "type": "log_sink",
       "layer": 1,
       "domain": [
        "log_sink"
       ],
       "root_permitted": false,
       "sink_permitted": false
      }
     ],
     "edges": [
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "ingest_api",
       "v": "billing_core",
       "modality": "FORBID",
       "label": "calls",
       "active": true
      },
      {
       "u": "billing_core",
       "v": "audit_buffer",
       "modality": "REQ",
       "label": "flushes_to",
       "active": true
      },
      {
       "u": "ingest_api",
       "v": "metrics_hub",
       "modality": "REQ",
       "label": "emits_to",
       "active": true
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "WELD[queue_mgr|retry_daemon]",
       "modality": "REQ",
       "label": "calls_back",
       "active": false
      },
      {
       "u": "WELD[queue_mgr|retry_daemon]",
       "v": "billing_core",
       "modality": "REQ",
       "label": "calls",
       "active": true
      }
     ]
    },
    "log": []
   }
  ]
 },
 "final": {
  "status": "CANONICAL",
  "psi": [
   0,
   0,
   0,
   0
  ],
  "errors": [],
  "snapshot": {
   "nodes": [
    {
     "id": "WELD[queue_mgr|retry_daemon]",
     "status": "KNOWN",
     "type": "composite",
     "layer": 1,
     "domain": [],
     "root_permitted": true,
     "sink_permitted": false
    },
    {
     "id": "audit_buffer",
     "status": "KNOWN",
     "type": "log_sink",
     "layer": 1,
     "domain": [
      "log_sink",
      "service"
     ],
     "root_permitted": false,
     "sink_permitted": false
    },
    {
     "id": "billing_core",
     "status": "KNOWN",
     "type": "service",
     "layer": 1,
     "domain": [],
     "root_permitted": false,
     "sink_permitted": false
    },
    {
     "id": "ingest_api",
     "status": "KNOWN",
     "type": "service",
     "layer": 1,
     "domain": [],
     "root_permitted": true,
     "sink_permitted": false
    },
    {
     "id": "metrics_hub",
     "status": "KNOWN",
     "type": "log_sink",
     "layer": 1,
     "domain": [
      "log_sink"
     ],
     "root_permitted": false,
     "sink_permitted": false
    }
   ],
   "edges": [
    {
     "u": "ingest_api",
     "v": "billing_core",
     "modality": "REQ",
     "label": "calls",
     "active": false
    },
    {
     "u": "ingest_api",
     "v": "billing_core",
     "modality": "FORBID",
     "label": "calls",
     "active": true
    },
    {
     "u": "billing_core",
     "v": "audit_buffer",
     "modality": "REQ",
     "label": "flushes_to",
     "active": true
    },
    {
     "u": "ingest_api",
     "v": "metrics_hub",
     "modality": "REQ",
     "label": "emits_to",
     "active": true
    },
    {
     "u": "WELD[queue_mgr|retry_daemon]",
     "v": "WELD[queue_mgr|retry_daemon]",
     "modality": "REQ",
     "label": "calls",
     "active": false
    },
    {
     "u": "WELD[queue_mgr|retry_daemon]",
     "v": "WELD[queue_mgr|retry_daemon]",
     "modality": "REQ",
     "label": "calls_back",
     "active": false
    },
    {
     "u": "WELD[queue_mgr|retry_daemon]",
     "v": "billing_core",
     "modality": "REQ",
     "label": "calls",
     "active": true
    }
   ]
  },
  "log_tail": [
   "[B2] welded SCC ['queue_mgr', 'retry_daemon'] (size=2) into 'WELD[queue_mgr|retry_daemon]'",
   "[A3] llm proposal 'P-004' resolved 'metrics_hub' as type=log_sink (source=llm; engine-accepted)",
   "[A3] llm proposal 'P-001' resolved 'audit_buffer' as type=log_sink (source=llm; engine-accepted)"
  ]
 }
};
