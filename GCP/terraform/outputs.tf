output "project_id" {
  description = "The GCP Project ID."
  value       = var.project_id
}

output "region" {
  description = "The GCP deployment region (domestic India location)."
  value       = var.region
}

output "model_armor_template_id" {
  description = "The ID of the Model Armor safety template."
  value       = var.template_id
}

output "model_armor_template_resource_name" {
  description = "Full resource name of the Model Armor template."
  value       = "projects/${var.project_id}/locations/${var.region}/templates/${var.template_id}"
}

output "service_account_email" {
  description = "Email of the Antigravity FSI Guard Service Account."
  value       = google_service_account.fsi_guard_sa.email
}

output "dlp_inspect_template_name" {
  description = "Full resource name of the Indian FSI Cloud DLP Inspection Template."
  value       = var.enable_cloud_dlp_integration ? google_data_loss_prevention_inspect_template.fsi_india_dlp_template[0].name : "N/A"
}

output "audit_log_bucket_id" {
  description = "The 7-year retention Cloud Logging Bucket ID."
  value       = var.create_audit_log_bucket ? google_logging_project_bucket_config.fsi_audit_bucket[0].bucket_id : "N/A"
}

output "antigravity_config_yaml_snippet" {
  description = "Configuration block ready to paste into config/config.yaml."
  value       = <<EOT
# Paste into config/config.yaml:
model_armor:
  enabled: true
  project_id: "${var.project_id}"
  location: "${var.region}"
  template_id: "${var.template_id}"
EOT
}
