# FIRE LOB STATUS: LOCKED

**Status**: LOCKED  
**Tag**: fire-lob-v1.0.0  
**Date**: 2025-12-16  
**Description**: Fire LOB stabilization complete. Baseline established for audits, bug comparisons, and future enhancements.

## 🚫 Locked Constraints
After the "fire-lob-v1.0.0" tag:
1.  **NO Schema Changes**: The database schema for Fire LOB tables is frozen.
2.  **NO Rate Logic Changes**: The core calculation logic (rating_engine.py, fire_premium_service.py) is frozen.
3.  **NO Silent CSV Edits**: Data files in `data/` must not be modified without a formal migration process.

## ✅ Allowed Actions
1.  **🔧 Bug Fixes**: Critical bugs may be addressed with targeted patches.
2.  **🧪 Test Additions**: Expanding the test suite is encouraged.
3.  **🧾 Documentation**: Updates to documentation and reports are permitted.

## 🏗️ Architecture Baseline
- **Master Table**: `fire_add_on_master` (Canonical definition of add-ons)
- **Rates Table**: `fire_add_on_rates` (Special pricing overrides only)
- **Rate logic**: Separated into `rating_engine.py` (DB lookups) and `fire_premium_service.py` (Business logic, Premium calculation).
- **EQ Logic**: Enforced for applicable products / Zones; skipped for UBGR/BSUS.

## 🔗 Reference
- **Tag**: `fire-lob-v1.0.0`
- **Master CSV**: `data/fire_add_on_master.csv`
- **Rates CSV**: `data/fire_add_on_rates.csv`
