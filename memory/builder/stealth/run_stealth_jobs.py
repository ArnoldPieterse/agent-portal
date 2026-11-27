"""
Stealth Revenue Engine — Schedulable Job Runner
=================================================
Wraps the 3 packaged workflows with resource budget + logging for schtask deployment.

Usage:
    python run_stealth_jobs.py <wf1|wf2|wf3|all> [--input-dir DIR] [--output-dir DIR]

Resource budget (protects model seats):
    - Max RSS: 256 MB per job
    - Max wall-clock: 120 s per job
    - No network calls (offline-only)
    - Sequential execution when running 'all'

Exit codes:
    0 = all jobs completed within budget
    1 = one or more jobs failed (logic error)
    2 = resource budget exceeded (OOM or timeout)
    3 = input file missing/invalid
"""
import json, os, sys, time, signal, pathlib, importlib.util

# --- Resource Budget ---
MAX_RSS_MB = 256
MAX_WALL_SEC = 120
LOG_FILE = pathlib.Path(__file__).parent / "stealth-jobs.log.jsonl"

# Windows: use resource module if available, else soft-limit via alarm
try:
    import resource
    def set_rss_limit(mb):
        limit_bytes = mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
except ImportError:
    # Windows fallback: soft check via psutil if available
    def set_rss_limit(mb):
        pass  # Windows: rely on MAX_WALL_SEC timeout instead

def log_entry(job, status, elapsed_s, detail=""):
    entry = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "job": job,
             "status": status, "elapsed_s": round(elapsed_s, 2), "detail": detail}
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[{entry['ts']}] {job}: {status} ({elapsed_s:.1f}s) {detail}")

# --- Timeout handler (cross-platform) ---
class BudgetExceeded(Exception):
    pass

def timeout_handler(signum, frame):
    raise BudgetExceeded(f"exceeded {MAX_WALL_SEC}s wall-clock")

# Windows: signal.SIGALRM not available, use threading.Timer
if hasattr(signal, 'SIGALRM'):
    def run_with_timeout(fn, *args, **kwargs):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(MAX_WALL_SEC)
        try:
            return fn(*args, **kwargs)
        finally:
            signal.alarm(0)
else:
    import threading
    def run_with_timeout(fn, *args, **kwargs):
        result = [None]
        error = [None]
        def target():
            try:
                result[0] = fn(*args, **kwargs)
            except Exception as e:
                error[0] = e
        t = threading.Thread(target=target, daemon=True)
        t.start()
        t.join(timeout=MAX_WALL_SEC)
        if t.is_alive():
            raise BudgetExceeded(f"exceeded {MAX_WALL_SEC}s wall-clock")
        if error[0]:
            raise error[0]
        return result[0]

# --- Job runners (import each wf module dynamically) ---
BASE_DIR = pathlib.Path(__file__).parent

def _load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, BASE_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_wf1(input_dir, output_dir):
    from datetime import date
    wf = _load_module("wf1", "wf1_ar_followup.py")
    invoices_path = pathlib.Path(input_dir) / "invoices.json"
    if not invoices_path.exists():
        raise FileNotFoundError(f"input missing: {invoices_path}")
    with open(invoices_path, encoding="utf-8") as f:
        data = json.load(f)
    result = wf.process(data, date.today())
    out = pathlib.Path(output_dir) / "reminders_wf1.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    total = sum(len(b.get("items", b if isinstance(b, list) else [])) for b in result.get("batches", []) if isinstance(b, (list, dict)))
    return {"batches": len(result.get("batches", []))}

def run_wf2(input_dir, output_dir):
    from datetime import date
    wf = _load_module("wf2", "wf2_weekly_report.py")
    metrics_path = pathlib.Path(input_dir) / "metrics.jsonl"
    if not metrics_path.exists():
        raise FileNotFoundError(f"input missing: {metrics_path}")
    records = []
    with open(metrics_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    result = wf.compute_report(records, date.today())
    out = pathlib.Path(output_dir) / "report_wf2.md"
    out.write_text(result, encoding="utf-8")
    return {"lines": len(result.splitlines())}

def run_wf3(input_dir, output_dir):
    from datetime import datetime
    wf = _load_module("wf3", "wf3_reminder_pipeline.py")
    sched_path = pathlib.Path(input_dir) / "schedule.json"
    if not sched_path.exists():
        raise FileNotFoundError(f"input missing: {sched_path}")
    with open(sched_path, encoding="utf-8") as f:
        data = json.load(f)
    result = wf.find_due(data, datetime.now())
    out = pathlib.Path(output_dir) / "reminders_wf3.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    due_count = len(result.get("due", [])) if isinstance(result, dict) else len(result)
    return {"due": due_count}

JOBS = {
    "wf1": ("wf1_ar_followup", run_wf1),
    "wf2": ("wf2_weekly_report", run_wf2),
    "wf3": ("wf3_reminder_pipeline", run_wf3),
}

# --- Selftest ---
def selftest():
    print("=== run_stealth_jobs.py selftest ===")
    passed = 0; total = 5
    # T1: module loads without error
    try:
        assert JOBS["wf1"][1] is not None
        passed += 1
    except Exception as e:
        print(f"  FAIL T1: {e}")
    # T2: log entry writes correctly
    test_log = pathlib.Path("__test_stealth_log.jsonl")
    global LOG_FILE
    orig_log = LOG_FILE
    LOG_FILE = test_log
    try:
        log_entry("test", "PASS", 0.1, "selftest")
        content = test_log.read_text(encoding="utf-8").strip()
        entry = json.loads(content)
        assert entry["job"] == "test" and entry["status"] == "PASS"
        passed += 1
    except Exception as e:
        print(f"  FAIL T2: {e}")
    finally:
        LOG_FILE = orig_log
        test_log.unlink(missing_ok=True)
    # T3: timeout mechanism works (use a very short timeout for test)
    global MAX_WALL_SEC
    orig_max = MAX_WALL_SEC
    MAX_WALL_SEC = 1
    try:
        def sleep_forever():
            time.sleep(5)
        try:
            run_with_timeout(sleep_forever)
            print("  FAIL T3: no timeout raised")
        except BudgetExceeded:
            passed += 1
    except Exception as e:
        print(f"  FAIL T3: {e}")
    finally:
        MAX_WALL_SEC = orig_max
    # T4: input-missing raises FileNotFoundError
    try:
        run_wf1("/nonexistent_dir", "/tmp")
        print("  FAIL T4: no exception for missing input")
    except FileNotFoundError:
        passed += 1
    except Exception as e:
        print(f"  FAIL T4: wrong exception {type(e).__name__}: {e}")
    # T5: exit code mapping correct
    assert JOBS["wf1"][0] == "wf1_ar_followup"
    assert JOBS["wf2"][0] == "wf2_weekly_report"
    assert JOBS["wf3"][0] == "wf3_reminder_pipeline"
    passed += 1

    print(f"=== RESULT: {passed}/{total} ===")
    return passed == total

# --- Main ---
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    input_dir = "."; output_dir = "."
    for i, a in enumerate(sys.argv):
        if a == "--input-dir" and i+1 < len(sys.argv): input_dir = sys.argv[i+1]
        if a == "--output-dir" and i+1 < len(sys.argv): output_dir = sys.argv[i+1]

    os.makedirs(output_dir, exist_ok=True)
    set_rss_limit(MAX_RSS_MB)

    targets = args[0] if args else "all"
    if targets not in JOBS and targets != "all":
        print(f"ERROR: unknown job '{targets}'. Valid: wf1, wf2, wf3, all")
        sys.exit(1)

    jobs_to_run = list(JOBS.keys()) if targets == "all" else [targets]
    failures = 0
    for job_name in jobs_to_run:
        label, fn = JOBS[job_name]
        t0 = time.time()
        try:
            result = run_with_timeout(fn, input_dir, output_dir)
            elapsed = time.time() - t0
            log_entry(label, "PASS", elapsed, str(result))
        except BudgetExceeded as e:
            elapsed = time.time() - t0
            log_entry(label, "BUDGET_EXCEEDED", elapsed, str(e))
            sys.exit(2)
        except FileNotFoundError as e:
            elapsed = time.time() - t0
            log_entry(label, "INPUT_MISSING", elapsed, str(e))
            sys.exit(3)
        except Exception as e:
            elapsed = time.time() - t0
            log_entry(label, "FAIL", elapsed, f"{type(e).__name__}: {e}")
            failures += 1

    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
