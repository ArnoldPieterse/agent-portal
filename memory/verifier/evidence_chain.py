#!/usr/bin/env python3
"""Evidence hash chain — SHA256-chained verification log, tamper-evident from genesis."""
import hashlib, json, time, os, copy, sys

CHAIN_FILE = os.path.join(os.path.dirname(__file__), 'evidence_chain.json')

def sha256(data):
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def _entry_hash(entry):
    """Compute hash for an entry (excluding the 'hash' field itself)."""
    payload = {k: v for k, v in entry.items() if k != 'hash'}
    return sha256(json.dumps(payload, sort_keys=True))

def load_chain():
    if os.path.exists(CHAIN_FILE):
        with open(CHAIN_FILE, 'r') as f:
            return json.load(f)
    # Genesis block
    genesis = {
        'seq': 0,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'event': 'GENESIS',
        'detail': 'Evidence hash chain initialized for Verifier verification logs',
        'prev_hash': '0' * 64,
        'hash': None
    }
    genesis['hash'] = _entry_hash(genesis)
    chain = [genesis]
    _save_chain(chain)
    return chain

def _save_chain(chain):
    with open(CHAIN_FILE, 'w') as f:
        json.dump(chain, f, indent=2)

def append_entry(event, detail):
    chain = load_chain()
    last = chain[-1]
    entry = {
        'seq': last['seq'] + 1,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'event': event,
        'detail': detail,
        'prev_hash': last['hash'],
        'hash': None
    }
    entry['hash'] = _entry_hash(entry)
    chain.append(entry)
    _save_chain(chain)
    return entry

def validate_chain(data=None):
    """Validate a chain (list of entries). Returns {valid, entries, errors}."""
    if data is None:
        data = load_chain()
    errors = []
    for i, entry in enumerate(data):
        computed = _entry_hash(entry)
        if computed != entry['hash']:
            errors.append(f'Entry {i} (seq {entry["seq"]}): HASH MISMATCH')
        if i > 0 and entry['prev_hash'] != data[i-1]['hash']:
            errors.append(f'Entry {i} (seq {entry["seq"]}): CHAIN BREAK at link to prev')
    return {'valid': len(errors) == 0, 'entries': len(data), 'errors': errors}

if __name__ == '__main__':
    chain = load_chain()
    last_seq = chain[-1]['seq']
    print(f'Chain loaded: {len(chain)} entries (last seq={last_seq})')

    # Seed with today's evidence if not already present
    events = [
        ('REGRESSION_5PT_PASS', '5-point regression PASS on agent_portal.py sha1=418a57eec190 (2026-11-16); all 38 routes intact, WEDGE guard active'),
        ('SELF_CERT_AUDIT', 'Self-cert audit 2026-11-16: 28/60 markers clean (47%); Scribe 1/10, Designer 3/8 flagged; evidence memory/verifier/self-cert-audit-2026-11-16.md'),
    ]
    for i, (ev, det) in enumerate(events, start=1):
        if last_seq < i:
            e = append_entry(ev, det)
            print(f'  Appended seq {e["seq"]}: {e["event"]}')

    # Validate intact chain
    result = validate_chain()
    print(f'\n=== VALIDATION (intact) ===')
    print(f'  Valid: {result["valid"]} | Entries: {result["entries"]}')

    # Tamper test: mutate entry 0 detail, show detection
    tampered = copy.deepcopy(load_chain())
    if len(tampered) > 1:
        tampered[0]['detail'] = 'TAMPERED - original content destroyed'
        t_result = validate_chain(data=tampered)
        print(f'\n=== VALIDATION (tampered entry 0) ===')
        print(f'  Valid: {t_result["valid"]} | Errors: {len(t_result["errors"])}')
        for err in t_result['errors']:
            print(f'    - {err}')
        # Also verify entry 1 chain link is flagged
        if len(tampered) > 2:
            tampered[1]['prev_hash'] = 'f' * 64  # break the link too
            t2 = validate_chain(data=tampered)
            print(f'\n=== VALIDATION (tampered entries 0+1 link) ===')
            print(f'  Valid: {t2["valid"]} | Errors: {len(t2["errors"])}')
            for err in t2['errors']:
                print(f'    - {err}')
