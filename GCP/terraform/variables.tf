variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID where Model Armor and compliance infrastructure will be provisioned."
  default     = "stratosphere-461622"
}

variable "region" {
  type        = string
  description = "The Google Cloud region for Model Armor and DLP. Defaults to 'asia-south1' (Mumbai) for production RBI/SEBI domestic data residency, or 'us-central1' / supported regions for Argolis and sandbox environments."
  default     = "asia-south1"

  validation {
    condition     = contains(["asia-south1", "asia-south2", "us-central1", "us-east4", "europe-west1", "asia-southeast1"], var.region)
    error_message = "Region must be one of 'asia-south1', 'asia-south2', 'us-central1', 'us-east4', 'europe-west1', or 'asia-southeast1'."
  }
}

variable "template_id" {
  type        = string
  description = "Unique resource identifier for the Model Armor safety template."
  default     = "fsi-india-compliance-template"
}

variable "template_display_name" {
  type        = string
  description = "Human-readable display name for the Model Armor template."
  default     = "India FSI Governance & Safety Template"
}

variable "service_account_id" {
  type        = string
  description = "Account ID for the dedicated Antigravity Agent Service Account."
  default     = "antigravity-fsi-guard-sa"
}

variable "pi_jb_enforcement" {
  type        = string
  description = "Filter enforcement mode for Prompt Injection & Jailbreak attacks (ENFORCE or OFF)."
  default     = "ENFORCE"
}

variable "pi_jb_confidence_level" {
  type        = string
  description = "Minimum confidence threshold to trigger Prompt Injection & Jailbreak blocking (LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH)."
  default     = "LOW_AND_ABOVE"
}

variable "rai_hate_speech_confidence" {
  type        = string
  description = "Threshold for Responsible AI Hate Speech filter."
  default     = "MEDIUM_AND_ABOVE"
}

variable "rai_harassment_confidence" {
  type        = string
  description = "Threshold for Responsible AI Harassment filter."
  default     = "MEDIUM_AND_ABOVE"
}

variable "rai_sexual_content_confidence" {
  type        = string
  description = "Threshold for Responsible AI Sexually Explicit content filter."
  default     = "LOW_AND_ABOVE"
}

variable "rai_dangerous_content_confidence" {
  type        = string
  description = "Threshold for Responsible AI Dangerous Content filter."
  default     = "LOW_AND_ABOVE"
}

variable "enable_malicious_uri_filter" {
  type        = bool
  description = "Enable real-time interception of malicious and phishing URLs in prompts."
  default     = true
}

variable "enable_multi_language" {
  type        = bool
  description = "Enable native multi-language detection for Indian scheduled languages."
  default     = true
}

variable "enable_cloud_dlp_integration" {
  type        = bool
  description = "Provision a tailored Cloud DLP Inspection Template for Indian sensitive financial and identity infoTypes."
  default     = true
}

variable "create_audit_log_bucket" {
  type        = bool
  description = "Create a dedicated Cloud Logging Bucket with 7-year retention policy (RBI ITG 2023 Para 22 compliance)."
  default     = true
}

variable "audit_retention_days" {
  type        = number
  description = "Log retention period in days (2555 days = 7 years for RBI & SEBI compliance)."
  default     = 2555
}
