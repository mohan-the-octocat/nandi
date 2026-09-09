---
name: fsi-compliance-audit
description: >-
  Audits agent workflows, system prompts, data pipelines, and tool executions
  for compliance with Reserve Bank of India (RBI) IT Governance Directions (2023),
  SEBI Cyber Security and Cyber Resilience Framework (CSCRF 2024), and Digital
  Personal Data Protection (DPDP) Act 2023.
---

# FSI Compliance Audit Skill for India Regulated Entities

This skill provides step-by-step procedures to audit and verify that an Antigravity agent or application strictly conforms to Indian financial regulatory governance standards.

## Audit Workflow

### 1. Run Compliance Self-Verification
Execute the GRC administrator CLI to inspect all active controls:
```bash
python3 src/cli/grc_admin.py verify-compliance --framework ALL
```

### 2. Audit Active Prompt or Workflow
Test candidate prompts, tool arguments, or query templates against the dual-layer safety engine:
```bash
python3 src/cli/grc_admin.py test-prompt "Sample user prompt containing financial query"
```

### 3. Verify Cryptographic Audit Trail
Inspect the last 20 audit events and verify SHA-256 hash-chain integrity:
```bash
python3 src/cli/grc_admin.py show-audit --tail 20
```

## Regulatory References
* [RBI Master Direction on IT Governance (2023)](./references/rbi_master_direction.md)
* [SEBI CSCRF Framework (2024)](./references/sebi_cscrf_framework.md)
