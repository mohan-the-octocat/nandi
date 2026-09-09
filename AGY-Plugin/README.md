# Nandi - Antigravity Plugin (AGY-Plugin)

This directory contains the **Nandi (The Incorruptible Threshold Guardian)** plugin componentry for Google Antigravity.

Nandi operates directly within the developer's Antigravity IDE environment, inspecting prompts and tool executions in real-time through lifecycle hooks to enforce strict Indian Financial Services Institution (FSI) compliance and AI guardrails.

---

## Directory Layout

```
AGY-Plugin/
├── bin/                             # Plugin installer automation
│   └── install-nandi.sh             # 5-step installer (installs AGY-Plugin into IDE)
├── config/                          # Local policy & pattern configurations
│   ├── config.yaml                  # Master plugin configuration
│   ├── model_armor_policy.json      # Model Armor decision thresholds & mappings
│   ├── pii_patterns.json            # Indian PII regex patterns & checksum configs
│   ├── rbi_compliance.yaml          # RBI IT Governance control mapping
│   └── sebi_compliance.yaml         # SEBI CSCRF control mapping
├── hooks.json                       # Antigravity hook registrations (PreInvocation, PreToolUse)
├── logs/                            # Local tamper-evident audit logs
│   ├── .gitkeep
│   └── fsi_audit.log                # Cryptographic SHA-256 forward-chained audit trail
├── plugin.json                      # Antigravity plugin manifest
├── rules/                           # Ambient developer compliance rules
│   ├── pii_handling.md              # PII detection & masking rules
│   ├── rbi_governance.md            # RBI IT governance & security rules
│   └── sebi_governance.md           # SEBI CSCRF algorithmic oversight rules
├── skills/                          # Interactive compliance skills
│   ├── fsi-compliance-audit/        # Regulatory self-verification & audit skill
│   └── model-armor-diagnostics/     # Model Armor testing & benchmark skill
└── src/                             # Core Python implementation (Zero external dependencies)
    ├── cli/                         # GRC Administration CLI (grc_admin.py)
    ├── governance/                  # Audit logging & regulatory control mappings
    ├── hooks/                       # Antigravity lifecycle hook handlers
    ├── model_armor/                 # Google Cloud Model Armor REST client & evaluator
    └── pii_guard/                   # High-performance PII detector & checksum validators
```

---

## Core Capabilities

1. **Dual-Stage Lifecycle Hook Enforcement**:
   - **`PreInvocation`**: Sanitizes incoming user prompts against Google Cloud Model Armor before they reach the model. Enforces **strict fail-closed security** (blocks propagation if authentication or API check fails).
   - **`PreToolUse`**: Intercepts tool execution arguments (e.g. `run_command`, `replace_file_content`, `write_to_file`) to prevent Indian PII exposure or prompt injection payload execution.

2. **Indian PII Regex & Algorithmic Checksum Engine**:
   - **Aadhaar**: Verhoeff D5 mathematical checksum validation.
   - **PAN**: 5th character entity classification (P=Individual, C=Company, H=HUF, F=Firm, T=Trust).
   - **GSTIN**: 15-character Mod-36 checksum verification.
   - **Cards**: Luhn (Mod-10) algorithm validation for RuPay, Visa, Mastercard.
   - **Banking**: CBS Account structure, IFSC code validation, UPI VPA syntax.

3. **Google Cloud Model Armor Integration**:
   - Regional Endpoints (`modelarmor.{region}.rep.googleapis.com`)
   - Prompt Injection & Jailbreak detection (`LOW_AND_ABOVE` confidence)
   - Responsible AI (RAI) safety filters
   - Malicious URI and phishing link defense
   - Native ADC authentication with in-process or gcloud fallback

4. **Cryptographic Forward-Chained Audit Trail**:
   - Every security event is hashed with SHA-256 linking to the previous event hash (`prev_event_hash`).
   - Conforms to **RBI Master Direction (2023)** and **SEBI CSCRF (2024)** requirements for immutable, tamper-evident log preservation.

---

## Installation & Runtime

The client plugin is installed and managed via the installer script:

```bash
# Default: Installs with hermetic isolated virtual environment (.venv)
./AGY-Plugin/bin/install-nandi.sh

# Project-scoped installation (isolated to a single project):
./AGY-Plugin/bin/install-nandi.sh -p /path/to/my-project

# System Python override:
./AGY-Plugin/bin/install-nandi.sh --system
```

When installed, only this `AGY-Plugin/` directory is symlinked into Antigravity (`~/.gemini/config/plugins/nandi` or `<project>/_agents/plugins/nandi`). Server-side GCP infrastructure templates (`GCP/`) remain external and uninstalled.
