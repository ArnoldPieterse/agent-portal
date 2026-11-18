#!/usr/bin/env python3
"""Run breakpoint_gate.py --selftest with proper file context."""
import sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.argv = ["breakpoint_gate.py", "--selftest"]
# Now import and run
import importlib.util
spec = importlib.util.spec_from_file_location("bp", "memory/designer/breakpoint_gate.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
import asyncio
rc = asyncio.run(mod.main())
sys.exit(rc)
