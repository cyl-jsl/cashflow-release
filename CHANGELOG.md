# Changelog

All notable changes to this project will be documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [v0.3.0] - 2026-05-05

### New Features
- feat(skill): safety-first available amount format (fcdc4cc)
- feat(frontend): income-adjustment UI on Incomes page (31b8027)
- feat: income-adjustment API (upsert/list/delete actuals) (c10a29c)
- feat: adjustment-aware income expansion in forecast and timeline (b4144c2)
- feat: add IncomeAdjustment Pydantic schemas (182f883)
- feat: migration - add income_adjustments table (3e1fbd5)
- feat: add IncomeAdjustment SQLAlchemy model (23f1a71)

### Other
- chore: bump version to v0.3.0 (673bdd5)
- docs(skill): document income-adjustment workflow (ef77dba)
- Merge branch 'feat/income-adjustments' (dea2b34)
- Preserve salary baselines while allowing per-payday actual overrides (7e69bed)

## [v0.2.0] - 2026-03-17

### Other
- chore: prepare for public release via cashflow-release repo (2026a90)
- chore: remove docs/ from version control (eadb87e)
