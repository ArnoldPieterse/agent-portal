@echo off
rem Daily stealth-ledger aggregator (created 2026-11-25, Orchestrator assist for Scribe G1 + own Day-7 checkpoint)
python C:\Projects\AgentPortal\memory\orchestrator\stealth_ledger_daily.py >> C:\Projects\AgentPortal\memory\builder\stealth\ledger-daily.log 2>&1
