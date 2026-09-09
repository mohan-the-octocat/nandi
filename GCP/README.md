# Nandi - Google Cloud Server Infrastructure

This directory contains all server-side Google Cloud Platform (GCP) infrastructure and configuration templates for **Nandi (The Incorruptible Threshold Guardian)**. 

These components are decoupled from the client developer plugin and are deployed centrally by cloud/DevSecOps teams to enforce Indian Financial Services Institution (FSI) compliance across all AI/developer workloads.

---

## Architecture Overview

```
                        Google Cloud Platform (Server Infrastructure)
                        ================================================
                                                │
                 ┌──────────────────────────────┼──────────────────────────────┐
                 ▼                              ▼                              ▼
    ┌─────────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐
    │   Google Cloud          │    │   Cloud DLP             │    │   Cloud Logging         │
    │   Model Armor           │    │   Inspection Template   │    │   7-Year Audit Bucket   │
    ├─────────────────────────┤    ├─────────────────────────┤    ├─────────────────────────┤
    │ • Prompt Injection      │    │ • Aadhaar (Verhoeff)    │    │ • 2,555-day retention  │
    │   & Jailbreak Filter    │    │ • PAN (Format & Entity) │    │ • Immutable audit sink  │
    │ • Responsible AI (RAI)  │    │ • GSTIN, Bank Accounts  │    │ • RBI Master Direction  │
    │ • Multi-Language Support│    │ • Payment Cards, UPI    │    │ • SEBI CSCRF Rule 6.2   │
    │ • Regional REP Endpoint │    │ • Centralized scanning  │    │ • Cryptographic hashes  │
    └─────────────────────────┘    └─────────────────────────┘    └─────────────────────────┘
                 ▲                              ▲                              ▲
                 │                              │                              │
                 └──────────────────────────────┴──────────────────────────────┘
                                                │
                                    Terraform Infrastructure
                                       (`GCP/terraform/`)
```

---

## Directory Contents

| Component | Path | Description |
|---|---|---|
| **Setup Shell Script** | [`setup-model-armor.sh`](./setup-model-armor.sh) | End-to-end automated provisioner: verifies tools, enables APIs, assigns IAM roles, deploys the template via REP REST API, and tests live sanitization. |
| **Terraform Module** | [`terraform/`](./terraform/) | Production-ready Terraform automation provisioning Model Armor, Cloud DLP, Cloud Logging audit bucket, and IAM bindings. |
| **Model Armor Template** | [`generated_model_armor_template.json`](./generated_model_armor_template.json) | Standalone JSON payload definition for the Model Armor template (used for REST/curl deployments). |
| **Model Armor Setup Guide** | [`MODEL_ARMOR_SETUP.md`](./MODEL_ARMOR_SETUP.md) | In-depth technical reference for Regional Endpoints, REST API invocation, and filter configuration. |

---

## Server-Side Managed Resources

### 1. Google Cloud Model Armor Template
- **Template ID**: `fsi-india-compliance-template`
- **Region**: `asia-south1` (Mumbai) or `us-central1`
- **Resource Name**: `projects/${PROJECT_ID}/locations/${REGION}/templates/fsi-india-compliance-template`
- **Regional Endpoint (REP)**: `modelarmor.${REGION}.rep.googleapis.com` (e.g., `modelarmor.asia-south1.rep.googleapis.com`)
- **Configured Filters**:
  - **Prompt Injection & Jailbreak**: `filter_enforcement: ENABLED`, `confidence_level: LOW_AND_ABOVE`
  - **Responsible AI (RAI)**: Hate speech, harassment, sexually explicit, and dangerous content filters set to `STRICT`
  - **Malicious URIs**: Proactive domain & phishing link detection (in supported regions)
  - **Multi-Language Detection**: Automatic language normalization and safety checks

### 2. Cloud DLP Inspection Template
- **Resource ID**: `projects/${PROJECT_ID}/locations/us-central1/inspectTemplates/4959499959065563928`
- **Inspect InfoTypes**: `INDIA_AADHAAR_NUMBER`, `INDIA_PAN_NUMBER`, `INDIA_GST_INDIVIDUAL`, `CREDIT_CARD_NUMBER`, `SWIFT_CODE`, `PHONE_NUMBER`, `EMAIL_ADDRESS`
- **Min Likelihood**: `LIKELY`

### 3. Regulatory 7-Year Cloud Logging Audit Bucket
- **Bucket ID**: `fsi-india-grc-audit-bucket`
- **Retention Period**: 2,555 days (7 years) strictly conforming to **RBI Master Direction on IT Governance (2023)** and **SEBI CSCRF (2024)**
- **Log Sink**: `fsi-india-grc-audit-sink` capturing all Nandi client audit logs and Model Armor sanitation telemetry

### 4. Service Account & IAM RBAC
- **Service Account**: `sa-nandi-guard@${PROJECT_ID}.iam.gserviceaccount.com`
- **Required Roles**:
  - `roles/modelarmor.user` (Allows prompt sanitization via `modelarmor.templates.sanitizeUserPrompt`)
  - `roles/modelarmor.viewer` (Allows template inspection via `modelarmor.templates.get`)
  - `roles/logging.bucketWriter` (Allows writing tamper-evident audit trails to regulatory storage)

---

## Deployment Instructions

### Option A: Automated Shell Script Deployment (Quickest & Recommended)

Run the end-to-end setup script:
```bash
# Automated setup (checks tools, enables APIs, configures IAM, deploys template, verifies with test prompt)
./GCP/setup-model-armor.sh

# Or with custom project and region
./GCP/setup-model-armor.sh --project your-gcp-project --region asia-south1
```

### Option B: Automated Terraform Deployment

1. Authenticate with Google Cloud:
   ```bash
   gcloud auth application-default login
   ```

2. Change to the Terraform directory:
   ```bash
   cd GCP/terraform
   ```

3. Configure your variables:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars and set your project_id, region, and admin identity
   ```

4. Initialize and apply:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

### Option C: Direct REST / gcloud API Deployment

If deploying without Terraform, use the pre-generated JSON template:

```bash
PROJECT_ID="$(gcloud config get-value project)"
REGION="asia-south1"
ENDPOINT="modelarmor.${REGION}.rep.googleapis.com"
TEMPLATE_ID="fsi-india-compliance-template"

# Enable required APIs
gcloud services enable modelarmor.googleapis.com dlp.googleapis.com logging.googleapis.com --project="${PROJECT_ID}"

# Create Model Armor Template via REST API
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "X-Goog-User-Project: ${PROJECT_ID}" \
  "https://${ENDPOINT}/v1/projects/${PROJECT_ID}/locations/${REGION}/templates?templateId=${TEMPLATE_ID}" \
  -d @GCP/generated_model_armor_template.json
```

---

## Compliance Reference

- **RBI Master Direction on IT Governance (2023)**: Sections 14, 22, 29 (Audit trail immutability, cyber defense, data localization).
- **SEBI CSCRF (2024)**: Section 3.2.1, Rule 6.2 (Input validation for AI/ML, zero trust, 7-year log retention).
- **Digital Personal Data Protection (DPDP) Act 2023**: Section 8 (Data fiduciary duties, sensitive personal data masking).
