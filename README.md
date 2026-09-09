# Nandi

[![Plugin: Nandi](https://img.shields.io/badge/Plugin-Nandi-purple)](plugin.json)
[![Compliance: RBI IT Governance 2023](https://img.shields.io/badge/Compliance-RBI%20IT%20Governance%202023-blue)](docs/RBI_COMPLIANCE.md)
[![Compliance: SEBI CSCRF 2024](https://img.shields.io/badge/Compliance-SEBI%20CSCRF%202024-green)](docs/SEBI_COMPLIANCE.md)
[![Compliance: DPDP Act 2023](https://img.shields.io/badge/Compliance-DPDP%20Act%202023-orange)](docs/RBI_COMPLIANCE.md)
[![Security: Google Cloud Model Armor](https://img.shields.io/badge/Security-Google%20Cloud%20Model%20Armor-red)](docs/MODEL_ARMOR_SETUP.md)
[![Test Suite: 100% Pass](https://img.shields.io/badge/Tests-31%2F31%20Passing-brightgreen)](tests/run_all_tests.py)

**Nandi** (*The Incorruptible Threshold Guardian*): Enterprise-grade Governance, Risk, and Compliance (GRC) Antigravity Plugin providing real-time **Indian PII Regex/Checksum Protection** and **Google Cloud Model Armor Safety Filtering** for Financial Services Institutions (Banks, NBFCs, Stock Brokers, AMCs, FinTechs) in India.

---

## Key Features

1. **Deterministic Indian PII Guard Hook (`PreInvocation` & `PreToolUse`)**:
   - **UIDAI Aadhaar**: 12-digit number validated via **Verhoeff Dihedral Group D5** algorithm.
   - **Income Tax PAN**: 10-character alphanumeric with entity character classification (`P`, `C`, `H`, `F`, `A`, `T`, `B`, `L`, `J`, `G`).
   - **Payment Cards**: 16-digit RuPay, Visa, Mastercard with **Luhn Mod-10** verification.
   - **GSTIN**: 15-character identifier with state prefix and **Mod 36** checksum.
   - **Banking Data**: Core Banking Account numbers, IFSC codes, MICR codes.
   - **NPCI UPI VPA**: Real-time validation of bank handles (`@okaxis`, `@okhdfcbank`, `@oksbi`, `@paytm`, etc.).
   - **Identity & Contact**: Indian Driving Licences (Sarathi format), Passports, Voter ID (EPIC), PIN codes, CIN, Phone numbers.

2. **Google Cloud Model Armor Safety Hook (`PreInvocation` & `PreToolUse`)**:
   - **Prompt Injection & Jailbreak (PI/JB)**: Intercepts direct/indirect instruction overrides, developer mode exploits, and system prompt leakage attacks.
   - **Responsible AI (RAI)**: Filters hate speech, harassment, dangerous content, and toxicity.
   - **Malicious URIs & Phishing**: Intercepts unapproved external links and malware distribution vectors.
   - **Multi-Lingual Support**: Native detection across English and Indian languages (Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada).
   - **Fail-Closed Security**: High-availability resilience defaulting to deny on security anomalies.

3. **Tamper-Resistant Cryptographic Audit Trail**:
   - Every prompt evaluation and hook decision is recorded with a **SHA-256 cryptographic hash chain**.
   - Dual UTC & IST timestamps formatted for 7-year regulatory retention under RBI and SEBI rules.

4. **Complete Regulatory Rules & Skills**:
   - Workspace rules (`rules/rbi_governance.md`, `rules/sebi_governance.md`, `rules/pii_handling.md`).
   - Interactive diagnostic skills (`fsi-compliance-audit`, `model-armor-diagnostics`).
   - Administrative CLI tool (`src/cli/grc_admin.py`).

---

## Installation & Setup in Local Antigravity 2.0

### Method 1: Automated Installer (Recommended)
Clone the repository and run the automated installer script:
```bash
git clone https://github.com/mohan-the-octocat/nandi.git
cd nandi
./bin/install-nandi.sh
```

By default, the installer provisions an isolated, hermetic virtual environment at `<PLUGIN_ROOT>/.venv` and installs optional acceleration packages (`google-auth`, `pyyaml`).

To override and use host system Python instead of `.venv`:
```bash
./bin/install-nandi.sh --system
```

To install scoped to a specific project alone:
```bash
./bin/install-nandi.sh --project-dir /path/to/your/project-workspace
```

The installer:
1. **Performs Local Environment & Runtime Diagnostics**: Verifies host Python 3.8+, provisions an isolated `.venv` environment (or uses host Python if `--system` is specified), validates core standard library modules (`dataclasses`, `hashlib`, `json`, `urllib`, etc.), installs/probes optional acceleration packages (`google-auth`, `pyyaml`), checks `gcloud` CLI presence/account/project, and verifies repository file integrity.
2. **Authenticates**: Runs `gcloud auth application-default login` to configure Application Default Credentials (ADC) for Model Armor.
3. **Validates GCP Project & Model Armor Template**: Validates regional REP endpoint reachability (`modelarmor.asia-south1.rep.googleapis.com`), checks existence and filter configurations of the Model Armor template (`fsi-india-compliance-template`), and executes a live prompt sanitization validation call.
4. **Runs Test Suite**: Validates all 31 automated unit tests across PII checksums, Model Armor gates, and governance using the selected runtime.
5. **Installs Plugin**: Binds the exact Python interpreter into `hooks.json`, configures symlinks, and registers lifecycle hooks in Antigravity.

### Method 2: Manual Symlink (Global)
```bash
ln -s /path/to/nandi ~/.gemini/config/plugins/nandi
```

### Method 3: Workspace-Scoped Installation (Project-specific)
To enforce GRC guardrails only within a specific project or workspace repository:
```bash
cd /path/to/your/project-workspace
mkdir -p .antigravity/plugins
git clone https://github.com/mohan-the-octocat/nandi.git .antigravity/plugins/nandi
```

### Method 3: Via Antigravity 2.0 UI Settings
1. Open your **Antigravity 2.0** desktop interface.
2. Open **Settings** (⚙️) from the sidebar or command palette (`Ctrl/Cmd + ,`).
3. Navigate to **Plugins & Customizations** > **Installed Plugins**.
4. Click **Add Plugin** > **Install from Git Repository**.
5. Paste the repository URL: `https://github.com/mohan-the-octocat/nandi.git`
6. Click **Install & Enable**.

---

### Troubleshooting Plugin Discovery

If the plugin does not appear in Antigravity after placing it in a global path:

1. **Explicit Registration via `plugins.json`**:
   If Antigravity does not automatically scan your custom directory, explicitly register the path in your global plugins configuration file (`~/.gemini/config/plugins.json`):
   ```json
   {
     "entries": [
       {
         "path": "/absolute/path/to/nandi"
       }
     ]
   }
   ```
2. **Verify `plugin.json` Location**:
   Ensure `plugin.json` is at the **root** of the target folder (`/path/to/nandi/plugin.json`) and not nested inside a subfolder.
3. **Permissions**:
   Ensure the hook entrypoints have executable permissions:
   ```bash
   chmod +x src/hooks/*.py src/cli/grc_admin.py bin/install-nandi.sh
   ```
4. **Session Refresh**:
   Plugins, hooks, and skills are initialized when a session starts. Open a **new conversation window** or restart Antigravity to reload the discovery index.

---

### Verifying Plugin Activation

Once installed, verify that the lifecycle hooks and guardrails are active:

1. **Verify Compliance Coverage**:
   ```bash
   python3 src/cli/grc_admin.py verify-compliance --framework ALL
   ```
2. **Run Health & Safety Probes**:
   ```bash
   python3 tests/run_all_tests.py
   ```
3. **Live Prompt Test**: In the Antigravity prompt bar, enter:
   ```
   Please verify account KYC for customer PAN ABCPE1234F and Aadhaar 2345 6789 0124
   ```
   The `fsi-pii-guard` hook will immediately intercept the prompt, preventing LLM exposure and displaying an RBI/SEBI governance block banner.

---

## Quickstart

### 1. Provision Server-Side Model Armor & Infrastructure via Terraform
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply
```

### 2. Run Automated Test Suite
```bash
python3 tests/run_all_tests.py
```

### 3. Test a Prompt with the Admin CLI
```bash
python3 src/cli/grc_admin.py test-prompt "Check KYC: PAN ABCPE1234F, Aadhaar 2345 6789 0124"
```

### 4. Verify Compliance Matrix
```bash
python3 src/cli/grc_admin.py verify-compliance --framework ALL
```

### 5. Inspect Cryptographic Audit Trail
```bash
python3 src/cli/grc_admin.py show-audit --tail 10
```

---

## Documentation Links

* [System Architecture & SDD](docs/ARCHITECTURE.md)
* [Terraform Infrastructure Automation](terraform/README.md)
* [RBI Master Direction Compliance Mapping](docs/RBI_COMPLIANCE.md)
* [SEBI CSCRF Framework Compliance Mapping](docs/SEBI_COMPLIANCE.md)
* [Google Cloud Model Armor Deployment Guide](docs/MODEL_ARMOR_SETUP.md)
* [Operator & Developer User Guide](docs/USER_GUIDE.md)

---

## License
Apache-2.0. Developed for Google Cloud Financial Services Customers.
