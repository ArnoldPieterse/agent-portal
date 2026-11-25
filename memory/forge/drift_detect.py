#!/usr/bin/env python3
"""drift_detect.py - Gate Pipeline Drift Detector (Forge Goal #10)

Monitors gate pipeline for silent degradation:
  1. New deps in modified scripts not in requirements.txt -> auto-add
  2. Test files added but not registered in test-topology.json -> flag
  3. Config schema changes not reflected in validation -> flag

Usage: python memory/forge/drift_detect.py [--fix] [--json]
Exit codes: 0 = clean (no drift), 1 = drift detected/fixed, 2 = unfixable items flagged
"""
import sys, os, re, json, ast, datetime, pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FORGE_DIR = os.path.join(ROOT, "memory", "forge")
OPS_DIR = os.path.join(ROOT, "memory", "ops")
REQUIREMENTS = os.path.join(ROOT, "requirements.txt")
TOPOLOGY = os.path.join(FORGE_DIR, "test-topology.json")
AGENTS_JSON = os.path.join(ROOT, "agents.json")
RESULT_JSON = os.path.join(FORGE_DIR, "drift_detect_last.json")

# Standard library modules (no need in requirements.txt)
STDLIB_MODULES = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else {
    'os','sys','re','json','ast','datetime','pathlib','subprocess','tempfile',
    'socket','urllib','http','time','shutil','hashlib','base64','struct',
    'threading','multiprocessing','concurrent','queue','collections','itertools',
    'functools','operator','math','random','string','textwrap','unicodedata',
    'copy','types','typing','abc','enum','dataclasses','contextlib','io',
    'codecs','pickle','shelve','marshal','pprint','reprlib','warnings',
    'logging','configparser','argparse','getopt','glob','fnmatch',
    'platform','errno','signal','select','selectors','asyncio','concurrent',
    'ctypes','builtins','__future__','site','zipfile','tarfile','gzip',
    'bz2','lzma','zlib','csv','xml','html','email','smtplib','poplib',
    'imaplib','ftplib','telnetlib','uuid','decimal','fractions','statistics',
    'array','bisect','heapq','weakref','gc','inspect','dis','traceback',
    'linecache','tokenize','token','compileall','py_compile','pkgutil',
    'importlib','zipimport','encodings','codeop','code','compileall',
    'secrets','hmac','ssl','getpass','locale','gettext',
    'calendar','timeit','profile','cProfile','pstats','atexit',
    'copyreg','pickletools','socketserver','mimetypes','netrc',
    'ntpath','posixpath','genericpath','stat','fileinput',
    'pydoc','webbrowser','cgi','cgitb','wsgiref',
    'sqlite3','dbm','zoneinfo','tomllib','graphlib'
}

# Known third-party packages that map to import names -> pip name
IMPORT_TO_PIP = {
    'requests': 'requests',
    'flask': 'flask',
    'fastapi': 'fastapi',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'yaml': 'pyyaml',
    'PIL': 'pillow',
    'cv2': 'opencv-python',
    'scipy': 'scipy',
    'matplotlib': 'matplotlib',
    'pytest': 'pytest',
    'playwright': 'playwright',
    'selenium': 'selenium',
    'paramiko': 'paramiko',
    'fabric': 'fabric',
    'docker': 'docker',
    'aiohttp': 'aiohttp',
    'httpx': 'httpx',
    'sqlalchemy': 'sqlalchemy',
    'redis': 'redis',
    'celery': 'celery',
}


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def extract_imports(filepath):
    """Extract top-level import module names from a Python file using AST."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=filepath)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return set()
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # absolute imports only
                imports.add(node.module.split('.')[0])
    return imports


def scan_scripts():
    """Scan all gate pipeline scripts for third-party imports."""
    all_imports = {}  # module_name -> list of files that import it
    
    script_dirs = [FORGE_DIR, OPS_DIR]
    for d in script_dirs:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith('.py'):
                continue
            filepath = os.path.join(d, f)
            imports = extract_imports(filepath)
            for imp in imports:
                if imp in STDLIB_MODULES or imp.startswith('_'):
                    continue
                rel = os.path.relpath(filepath, ROOT).replace('\\', '/')
                all_imports.setdefault(imp, []).append(rel)
    
    # Filter to known third-party (not local project modules)
    local_modules = set()
    for d in script_dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith('.py') and f != '__init__.py':
                local_modules.add(f[:-3])
    # Also check root-level modules
    for f in os.listdir(ROOT):
        if f.endswith('.py'):
            local_modules.add(f[:-3])
    
    third_party = {}
    for mod, files in all_imports.items():
        if mod not in local_modules and mod not in STDLIB_MODULES:
            pip_name = IMPORT_TO_PIP.get(mod, mod)
            third_party[pip_name] = {"import": mod, "used_by": files}
    
    return third_party


def check_requirements(third_party):
    """Check requirements.txt against discovered third-party imports."""
    missing = []
    existing = set()
    
    if os.path.isfile(REQUIREMENTS):
        with open(REQUIREMENTS, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Normalize: strip version specifiers
                    name = re.split(r'[>=<!~\[;]', line)[0].strip().lower()
                    existing.add(name)
    
    for pip_name, info in third_party.items():
        if pip_name.lower() not in existing:
            missing.append({"pip": pip_name, "import": info["import"], "used_by": info["used_by"]})
    
    return missing


def fix_requirements(missing):
    """Add missing packages to requirements.txt."""
    if not missing:
        return False
    lines = []
    if os.path.isfile(REQUIREMENTS):
        with open(REQUIREMENTS, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    
    # Add header if creating new file
    if not lines:
        lines.append("# Auto-generated by drift_detect.py - gate pipeline dependencies\n")
    
    added = []
    for item in missing:
        line = item["pip"] + "\n"
        if line not in lines:
            lines.append(line)
            added.append(item["pip"])
    
    with open(REQUIREMENTS, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return True


def check_test_registration():
    """Check for test files not registered in test-topology.json."""
    if not os.path.isfile(TOPOLOGY):
        return {"registered": [], "unregistered": [], "error": "test-topology.json missing"}
    
    with open(TOPOLOGY, 'r', encoding='utf-8') as f:
        topo = json.load(f)
    
    # Collect registered test IDs
    registered_ids = set()
    for host_name, host_cfg in topo.get('hosts', {}).items():
        for t in host_cfg.get('tests', []):
            registered_ids.add(t.get('id', ''))
    
    # Find test-like files in forge dir (test_*.py or *_test.py)
    test_files = []
    if os.path.isdir(FORGE_DIR):
        for f in sorted(os.listdir(FORGE_DIR)):
            if f.endswith('.py') and (f.startswith('test_') or f.endswith('_test.py')):
                test_files.append(f)
    
    unregistered = []
    for tf in test_files:
        # A test file is considered registered if its name (minus .py) appears
        # in any registered test ID, or if it's a standalone script referenced elsewhere
        stem = tf.replace('.py', '')
        if stem not in registered_ids and stem not in str(registered_ids):
            unregistered.append(tf)
    
    return {"registered": sorted(registered_ids), "test_files": test_files, "unregistered": unregistered}


def check_config_schema():
    """Check agents.json schema consistency."""
    issues = []
    if not os.path.isfile(AGENTS_JSON):
        issues.append("agents.json not found at root")
        return issues
    
    try:
        with open(AGENTS_JSON, 'r', encoding='utf-8') as f:
            agents = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"agents.json invalid JSON: {e}")
        return issues
    
    # Handle both formats: top-level list or {"agents": [...]}
    if isinstance(agents, dict):
        agents_list = agents.get('agents', [])
        if not isinstance(agents_list, list):
            issues.append("agents.json 'agents' key is not a list")
            return issues
    elif isinstance(agents, list):
        agents_list = agents
    else:
        issues.append(f"agents.json root is {type(agents).__name__}, expected list or dict with 'agents' key")
        return issues
    
    # Required fields per agent entry
    required = ['name', 'model_id']
    for i, agent in enumerate(agents_list):
        if not isinstance(agent, dict):
            issues.append(f"agents[{i}] is not an object")
            continue
        for field in required:
            if field not in agent:
                issues.append(f"agents[{i}] ({agent.get('name', '?')}) missing required field: {field}")
    
    return issues


def main():
    fix_mode = '--fix' in sys.argv
    json_mode = '--json' in sys.argv
    
    results = {
        "ts": now_iso(),
        "mode": "fix" if fix_mode else "detect",
        "checks": {},
        "drift_found": False,
        "items_fixed": [],
        "items_flagged": []
    }
    
    # Check 1: Dependencies
    print("[1/3] Scanning gate pipeline scripts for third-party imports...")
    third_party = scan_scripts()
    missing_deps = check_requirements(third_party)
    
    if missing_deps:
        results["drift_found"] = True
        dep_info = {"missing": missing_deps, "action": None}
        if fix_mode:
            fixed = fix_requirements(missing_deps)
            dep_info["action"] = f"added {len(missing_deps)} to requirements.txt" if fixed else "no changes"
            if fixed:
                results["items_fixed"].append(f"requirements.txt: +{', '.join(m['pip'] for m in missing_deps)}")
        else:
            dep_info["action"] = f"run with --fix to add {len(missing_deps)} missing deps"
        results["checks"]["dependencies"] = dep_info
        print(f"  Found {len(third_party)} third-party imports, {len(missing_deps)} missing from requirements.txt")
    else:
        results["checks"]["dependencies"] = {
            "status": "OK",
            "total_third_party": len(third_party),
            "all_in_requirements": True
        }
        print(f"  {len(third_party)} third-party imports, all in requirements.txt. OK")
    
    # Check 2: Test registration
    print("[2/3] Checking test file registration in topology...")
    test_reg = check_test_registration()
    if test_reg.get("unregistered"):
        results["drift_found"] = True
        results["checks"]["test_registration"] = test_reg
        results["items_flagged"].extend(
            [f"unregistered test file: {tf}" for tf in test_reg["unregistered"]]
        )
        print(f"  {len(test_reg['unregistered'])} test files not in topology: {test_reg['unregistered']}")
    else:
        results["checks"]["test_registration"] = {
            "status": "OK",
            "registered_tests": len(test_reg.get("registered", [])),
            "test_files_found": len(test_reg.get("test_files", []))
        }
        print(f"  {len(test_reg.get('registered', []))} registered tests, {len(test_reg.get('test_files', []))} test files. OK")
    
    # Check 3: Config schema
    print("[3/3] Validating agents.json schema...")
    schema_issues = check_config_schema()
    if schema_issues:
        results["drift_found"] = True
        results["checks"]["config_schema"] = {"status": "ISSUES", "issues": schema_issues}
        results["items_flagged"].extend(schema_issues)
        print(f"  {len(schema_issues)} schema issues found")
    else:
        results["checks"]["config_schema"] = {"status": "OK"}
        print("  agents.json schema valid. OK")
    
    # Save results
    with open(RESULT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    if json_mode:
        print(json.dumps(results, indent=2))
    else:
        status = "DRIFT DETECTED" if results["drift_found"] else "CLEAN"
        print(f"\n=== VERDICT: {status} ===")
        if results["items_fixed"]:
            print(f"  Fixed: {len(results['items_fixed'])} item(s)")
        if results["items_flagged"]:
            print(f"  Flagged (unfixable): {len(results['items_flagged'])} item(s)")
            for item in results["items_flagged"]:
                print(f"    - {item}")
    
    # Exit code: 0=clean, 1=drift found/fixed, 2=unfixable items
    if not results["drift_found"]:
        return 0
    elif results["items_flagged"] and not fix_mode:
        return 2
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
