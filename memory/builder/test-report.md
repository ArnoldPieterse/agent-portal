# Portal Test Report

**Run:** 2026-11-19 23:37 UTC | **Suite:** all | **Mode:** offline
**Result:** 41/42 passed (98%)

## api

- ✅ `fixture_load` (48 endpoints)
- ✅ `structure_valid`
- ✅ `route_coverage` (10 new routes not yet in fixture: ['/api/autoloop', '/api/evidence/quality', '/api/fleet/dependencies-graph'])
- ✅ `no_5xx_in_contract` (5xx: [])
- ✅ `schemas_nonempty` (empty: [])
- ✅ `critical:/api/chat` (not in fixture)
- ✅ `critical:/api/history` (not in fixture)
- ✅ `critical:/api/agents` (not in fixture)
- ✅ `critical:/api/goals` (not in fixture)
- ✅ `break_detection` (tamper not caught)
- ✅ `schema_types:/api/agents`
- ✅ `schema_types:/api/goals`
- ✅ `schema_types:/api/history`
- ✅ `baseline_integrity` (fixture drifted)
## ui

- ✅ `files_exist` (11 js, 3 css)
- ✅ `brace_balance:api-client.js` ({}=91/91(±3) ()=151/151)
- ✅ `brace_balance:components.js` ({}=2/0(±3) ()=14/13)
- ✅ `brace_balance:core.js` ({}=104/107(±3) ()=421/421)
- ✅ `brace_balance:fleet_health.js` ({}=32/32(±3) ()=62/62)
- ✅ `brace_balance:fleet_status.js` ({}=15/15(±3) ()=40/40)
- ✅ `brace_balance:fleet_topology.js` ({}=16/14(±3) ()=17/16)
- ✅ `brace_balance:icons.js` ({}=6/6(±3) ()=9/9)
- ✅ `brace_balance:notifications.js` ({}=22/22(±3) ()=87/87)
- ✅ `brace_balance:state.js` ({}=17/17(±3) ()=30/30)
- ✅ `brace_balance:tour.js` ({}=21/21(±3) ()=61/61)
- ✅ `brace_balance:uploads.js` ({}=119/121(±3) ()=481/480)
- ✅ `no_empty_rules:app.css` (0 empty)
- ✅ `no_empty_rules:app_density_before.css` (0 empty)
- ✅ `no_empty_rules:tokens.css` (0 empty)
- ❌ `component_usage:core.js` — createElement=7 (target<5), UI.*=27
- ✅ `state_module_exists`
- ✅ `state_wired_in_core`
- ✅ `error_boundary_present`
- ✅ `a11y_focus_visible`
## integration

- ✅ `agents_json_valid` (8 agents)
- ✅ `chat_endpoint_exists`
- ✅ `messages_endpoint_exists`
- ✅ `agents_endpoint_exists`
- ✅ `goals_endpoint_exists`
- ✅ `upload_endpoint_exists`
- ✅ `memory_endpoint_exists`
- ✅ `fleet_endpoint_exists`

**1 FAILURES:**
- `ui/component_usage:core.js`: createElement=7 (target<5), UI.*=27