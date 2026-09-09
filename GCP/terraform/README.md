# Terraform Automation for Google Cloud Model Armor & FSI Compliance Infrastructure

This Terraform module automates the entire server-side deployment of **Google Cloud Model Armor**, **Cloud DLP**, **IAM RBAC**, and **7-Year Cryptographic Audit Retention Buckets** in the customer's GCP environment, meeting all technical requirements for **RBI IT Governance (2023)** and **SEBI CSCRF (2024)**.

---

## 1. Resources Provisioned

```
+------------------------------------------------------------------------------------------+
|                                CUSTOMER GCP PROJECT                                       |
|                                                                                          |
|   +----------------------------------------------------------------------------------+   |
|   | 1. API Enablement: modelarmor, dlp, logging, monitoring, iam                     |   |
|   +----------------------------------------------------------------------------------+   |
|                                                                                          |
|   +----------------------------------------------------------------------------------+   |
|   | 2. Dedicated Service Account: antigravity-fsi-guard-sa                           |   |
|   |    Roles: roles/modelarmor.user, roles/modelarmor.viewer, roles/logging.logWriter|   |
|   +----------------------------------------------------------------------------------+   |
|                                                                                          |
|   +----------------------------------------------------------------------------------+   |
|   | 3. Model Armor Safety Template: (projects/*/locations/asia-south1/templates/*)   |   |
|   |    - Prompt Injection & Jailbreak (PI/JB) Defense: LOW_AND_ABOVE                 |   |
|   |    - Responsible AI (RAI) Content Filters: Hate, Harm, Sexual, Danger            |   |
|   |    - Malicious URI Interception (Phishing, Malware, Unapproved domains)          |   |
|   |    - Multi-Language Detection (English + 7 Indian Scheduled Languages)           |   |
|   +----------------------------------------------------------------------------------+   |
|                                                                                          |
|   +----------------------------------------------------------------------------------+   |
|   | 4. Cloud DLP Inspection Template:                                                |   |
|   |    - INDIA_AADHAAR_NUMBER, INDIA_PAN_NUMBER, INDIA_GST_INDIVIDUAL, CREDIT_CARD   |   |
|   +----------------------------------------------------------------------------------+   |
|                                                                                          |
|   +----------------------------------------------------------------------------------+   |
|   | 5. 7-Year Cloud Audit Log Bucket & Sink (RBI/SEBI 2555-Day Retention)           |   |
|   +----------------------------------------------------------------------------------+   |
+------------------------------------------------------------------------------------------+
```

---

## 2. Prerequisites

1. **Terraform CLI** `>= 1.5.0` installed.
2. **Google Cloud SDK (`gcloud`)** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
3. **Permissions**: GCP account needs `roles/owner` or `roles/editor` + `roles/resourcemanager.projectIamAdmin` on the target project.

---

## 3. Quickstart Deployment

### Step 1: Copy Variable Definitions
```bash
cp terraform.tfvars.example terraform.tfvars
```

### Step 2: Edit Configuration
Edit `terraform.tfvars` with your project ID:
```hcl
project_id = "your-gcp-project-id"
region     = "asia-south1" # Mumbai (or "asia-south2" Delhi)
```

### Step 3: Initialize & Plan
```bash
terraform init
terraform plan
```

### Step 4: Apply Infrastructure
```bash
terraform apply
```

### Step 5: Update Antigravity Plugin Configuration
After completion, Terraform will output the snippet to add to [`client/config/config.yaml`](../../client/config/config.yaml):
```yaml
model_armor:
  enabled: true
  project_id: "your-gcp-project-id"
  location: "asia-south1"
  template_id: "fsi-india-compliance-template"
```

---

## 4. Compliance Verification

| Regulatory Standard | Mandate | Terraform Resource |
| :--- | :--- | :--- |
| **RBI IT Governance 2023 (Para 11)** | Data Localization & Residency | `region = "asia-south1"` or `"asia-south2"` enforced via Terraform validation. |
| **RBI IT Governance 2023 (Para 14)** | Automated Adversarial Defense | `model_armor_template` with PI/JB & Malicious URI filtering enabled. |
| **RBI IT Governance 2023 (Para 22)** | 7-Year Log Retention | `google_logging_project_bucket_config.fsi_audit_bucket` with `retention_days = 2555`. |
| **SEBI CSCRF 2024 (Rule 6.2)** | Algorithmic Guardrails | Model Armor pre-processing gate + Cloud DLP Indian infoTypes inspection. |
