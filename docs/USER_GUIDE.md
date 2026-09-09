# Nandi - Operator & Developer User Guide

## 1. Overview

**Nandi** (*The Incorruptible Threshold Guardian*) automatically activates when installed in your Antigravity environment. It inspects all user prompts before they reach the model (`PreInvocation`), and inspects all tool executions (`PreToolUse`), guaranteeing strict compliance with Indian financial regulations.

---

## 2. Directory Structure

```
nandi/ (formerly grc-plugin/)
├── plugin.json                 # Antigravity plugin manifest
├── hooks.json                  # Lifecycle hook bindings (PreInvocation, PreToolUse)
├── config/
│   ├── config.yaml             # Global configuration (enforcement mode, thresholds)
│   ├── pii_patterns.json       # Indian PII regex patterns and checksum algorithms
│   ├── rbi_compliance.yaml     # RBI Master Direction mapping
│   ├── sebi_compliance.yaml    # SEBI CSCRF framework mapping
│   └── model_armor_policy.json # Model Armor template settings
├── src/
│   ├── pii_guard/              # Regex & Checksum PII engine (Verhoeff, Luhn, Mod 36)
│   ├── model_armor/            # Model Armor REST client and policy evaluator
│   ├── governance/             # Audit logger, RBI & SEBI controllers
│   ├── hooks/                  # Antigravity lifecycle hook executables
│   └── cli/                    # Admin CLI (grc_admin.py)
├── rules/                      # Always-on workspace rules (RBI & SEBI guidelines)
├── skills/                     # In-session skills (fsi-compliance-audit, model-armor-diagnostics)
├── tests/                      # 25+ automated unit, integration, and E2E test suites
└── docs/                       # Complete compliance & architectural documentation
```

---

## 3. CLI Administration & Diagnostics

### Test a Prompt against Guardrails
```bash
python3 src/cli/grc_admin.py test-prompt "Please check KYC for customer Aadhaar 2345 6789 0124 and PAN ABCPE1234F"
```

### Validate a Specific Entity Algorithm
```bash
# Validate Aadhaar Verhoeff checksum
python3 src/cli/grc_admin.py test-entity AADHAAR "2345 6789 0124"

# Validate Income Tax PAN
python3 src/cli/grc_admin.py test-entity PAN "ABCPE1234F"

# Validate GSTIN Mod 36
python3 src/cli/grc_admin.py test-entity GSTIN "27AADCS1234F1Z5"
```

### Inspect Tamper-Resistant Audit Log
```bash
python3 src/cli/grc_admin.py show-audit --tail 15
```

### Verify Regulatory Compliance Coverage
```bash
python3 src/cli/grc_admin.py verify-compliance --framework ALL
```

---

## 4. Running Test Suites

Execute the comprehensive test runner:
```bash
python3 tests/run_all_tests.py
```
