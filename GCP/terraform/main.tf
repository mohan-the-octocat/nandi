provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

provider "google-beta" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}

# ==============================================================================
# 1. API Services Activation
# ==============================================================================
locals {
  services = [
    "modelarmor.googleapis.com",
    "dlp.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com",
  ]
}

resource "google_project_service" "fsi_services" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ==============================================================================
# 2. Antigravity Agent Service Account & IAM RBAC
# ==============================================================================
resource "google_service_account" "fsi_guard_sa" {
  project      = var.project_id
  account_id   = var.service_account_id
  display_name = "Nandi Agent Service Account"
  description  = "Dedicated service account used by Antigravity runtime to invoke Model Armor and Cloud DLP."

  depends_on = [google_project_service.fsi_services]
}

resource "google_project_iam_member" "modelarmor_user" {
  project = var.project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:${google_service_account.fsi_guard_sa.email}"
}

resource "google_project_iam_member" "modelarmor_viewer" {
  project = var.project_id
  role    = "roles/modelarmor.viewer"
  member  = "serviceAccount:${google_service_account.fsi_guard_sa.email}"
}

resource "google_project_iam_member" "dlp_user" {
  count   = var.enable_cloud_dlp_integration ? 1 : 0
  project = var.project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.fsi_guard_sa.email}"
}

resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.fsi_guard_sa.email}"
}

# ==============================================================================
# 3. Cloud DLP Inspection Template (Indian Financial & Identity infoTypes)
# ==============================================================================
resource "google_data_loss_prevention_inspect_template" "fsi_india_dlp_template" {
  count        = var.enable_cloud_dlp_integration ? 1 : 0
  parent       = "projects/${var.project_id}/locations/${var.region}"
  description  = "Cloud DLP Inspection Template for Indian Financial Institutions (RBI & SEBI Compliance)."
  display_name = "FSI India Regulatory DLP Inspection Template"

  inspect_config {
    min_likelihood = "LIKELY"

    info_types {
      name = "INDIA_AADHAAR_INDIVIDUAL"
    }
    info_types {
      name = "INDIA_PAN_INDIVIDUAL"
    }
    info_types {
      name = "INDIA_GST_INDIVIDUAL"
    }
    info_types {
      name = "CREDIT_CARD_NUMBER"
    }
    info_types {
      name = "SWIFT_CODE"
    }
    info_types {
      name = "PHONE_NUMBER"
    }
    info_types {
      name = "EMAIL_ADDRESS"
    }

    limits {
      max_findings_per_item    = 100
      max_findings_per_request = 100
    }
  }

  depends_on = [google_project_service.fsi_services]
}

# ==============================================================================
# 4. Google Cloud Model Armor Template Provisioning
# ==============================================================================
locals {
  # Malicious URI filtering capability is currently supported in US/EU regions.
  # asia-south1 (Mumbai) / asia-south2 (Delhi) support PI/JB, RAI, and DLP domestic controls.
  include_malicious_uri = var.enable_malicious_uri_filter && !contains(["asia-south1", "asia-south2"], var.region)

  model_armor_payload = jsonencode({
    template_metadata = {
      custom_prompt_safety_error_message = "Prompt blocked by FSI Model Armor security policy."
      log_sanitize_operations            = var.enable_prompt_response_logging
      log_template_operations            = var.enable_template_operations_logging
      filter_version_selector = {
        alias = var.filter_version_alias
      }
    }
    filter_config = merge(
      {
        pi_and_jailbreak_filter_settings = {
          filter_enforcement = var.pi_jb_enforcement == "ENFORCE" ? "ENABLED" : "DISABLED"
          confidence_level   = var.pi_jb_confidence_level
        }
        rai_settings = {
          rai_filters = [
            {
              filter_type      = "HATE_SPEECH"
              confidence_level = var.rai_hate_speech_confidence
            },
            {
              filter_type      = "HARASSMENT"
              confidence_level = var.rai_harassment_confidence
            },
            {
              filter_type      = "SEXUALLY_EXPLICIT"
              confidence_level = var.rai_sexual_content_confidence
            },
            {
              filter_type      = "DANGEROUS"
              confidence_level = var.rai_dangerous_content_confidence
            }
          ]
        }
      },
      var.enable_basic_sdp ? {
        sdp_settings = {
          basic_config = {
            filter_enforcement = "ENABLED"
          }
        }
        } : {
        sdp_settings = {
          basic_config = {
            filter_enforcement = "DISABLED"
          }
        }
      },
      local.include_malicious_uri ? {
        malicious_uri_filter_settings = {
          filter_enforcement = "ENABLED"
        }
      } : {}
    )
  })
}

resource "local_file" "model_armor_spec" {
  filename = "${path.module}/generated_model_armor_template.json"
  content  = local.model_armor_payload
}

resource "null_resource" "model_armor_template_provisioner" {
  triggers = {
    project_id   = var.project_id
    region       = var.region
    template_id  = var.template_id
    payload_hash = sha256(local.model_armor_payload)
  }

  provisioner "local-exec" {
    command = <<EOT
      echo "Deploying Model Armor Template: projects/${var.project_id}/locations/${var.region}/templates/${var.template_id}..."
      
      TOKEN=$(gcloud auth print-access-token)
      if [ -z "$TOKEN" ]; then
        echo "Error: No gcloud credentials found. Please authenticate via 'gcloud auth login' and 'gcloud auth application-default login'." >&2
        exit 1
      fi

      # Check if template already exists
      HTTP_STATUS=$(curl -s -o /dev/null -w "%%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        -H "X-Goog-User-Project: ${var.project_id}" \
        "https://modelarmor.${var.region}.rep.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/templates/${var.template_id}")

      if [ "$HTTP_STATUS" -eq "200" ]; then
        echo "Template exists. Updating..."
        RESPONSE=$(curl -s -w "\nHTTP_CODE:%%{http_code}" -X PATCH \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json; charset=utf-8" \
          -H "X-Goog-User-Project: ${var.project_id}" \
          "https://modelarmor.${var.region}.rep.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/templates/${var.template_id}?updateMask=filter_config,template_metadata" \
          -d @${local_file.model_armor_spec.filename})
        echo "$RESPONSE"
      else
        echo "Creating new template..."
        RESPONSE=$(curl -s -w "\nHTTP_CODE:%%{http_code}" -X POST \
          -H "Authorization: Bearer $TOKEN" \
          -H "Content-Type: application/json; charset=utf-8" \
          -H "X-Goog-User-Project: ${var.project_id}" \
          "https://modelarmor.${var.region}.rep.googleapis.com/v1/projects/${var.project_id}/locations/${var.region}/templates?templateId=${var.template_id}" \
          -d @${local_file.model_armor_spec.filename})
        echo "$RESPONSE"
        if echo "$RESPONSE" | grep -q 'HTTP_CODE:200'; then
          echo "Template created successfully."
        else
          echo "Error: Failed to create template." >&2
          exit 1
        fi
      fi
EOT
  }

  depends_on = [
    google_project_service.fsi_services,
    local_file.model_armor_spec,
  ]
}

# ==============================================================================
# 5. Dedicated 7-Year Cloud Audit Log Bucket (RBI / SEBI Regulatory Mandate)
# ==============================================================================
resource "google_logging_project_bucket_config" "fsi_audit_bucket" {
  count          = var.create_audit_log_bucket ? 1 : 0
  project        = var.project_id
  location       = var.region
  bucket_id      = "fsi-india-compliance-audit-bucket"
  retention_days = var.audit_retention_days
  description    = "Cryptographically preserved 7-year audit retention bucket for RBI ITG 2023 (Para 22) and SEBI CSCRF 2024 (Rule 8.4) compliance."

  depends_on = [google_project_service.fsi_services]
}

resource "google_logging_project_sink" "fsi_audit_sink" {
  count                  = var.create_audit_log_bucket ? 1 : 0
  name                   = "fsi-india-grc-audit-sink"
  project                = var.project_id
  destination            = "logging.googleapis.com/projects/${var.project_id}/locations/${var.region}/buckets/${google_logging_project_bucket_config.fsi_audit_bucket[0].bucket_id}"
  filter                 = "resource.type=\"audited_resource\" OR jsonPayload.regulatory_frameworks:\"RBI_MD_IT_2023\" OR jsonPayload.regulatory_frameworks:\"SEBI_CSCRF_2024\""
  unique_writer_identity = true

  depends_on = [google_logging_project_bucket_config.fsi_audit_bucket]
}
