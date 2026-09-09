#!/usr/bin/env bash
# ==============================================================================
# Nandi Installer
# The Incorruptible Threshold Guardian for Google Antigravity.
#
# Execution Flow:
#  1. Local Environment & Library Diagnostics (Hermetic .venv by default, Python 3.8+, core stdlib, gcloud CLI, local files)
#  2. Google Cloud Authentication ('gcloud auth application-default login')
#  3. Google Cloud Project & Model Armor Template Diagnostics (REP endpoint, template inspection, live prompt sanitization)
#  4. Execute Unit Test Suite (31 tests)
#  5. Install Nandi plugin installables (Global or Project-Scoped)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLUGIN_ROOT="${REPO_ROOT}/client"
GCP_ROOT="${REPO_ROOT}/GCP"

GLOBAL_TARGET_DIR_1="${HOME}/.gemini/antigravity/plugins"
GLOBAL_TARGET_DIR_2="${HOME}/.gemini/config/plugins"

PROJECT_DIR=""
USE_VENV=true
RECREATE_VENV=false
SKIP_AUTH=false
SKIP_VALIDATION=false

print_usage() {
  cat <<EOF
Usage: ./bin/install-nandi.sh [OPTIONS]

Options:
  -p, --project-dir DIR    Install plugin scoped to a specific project alone (project-scoped)
  --system                 Use host system python3 instead of isolated .venv (override default)
  --recreate-venv          Recreate the isolated .venv environment from scratch
  --skip-auth              Skip interactive 'gcloud auth application-default login' (e.g. if already configured)
  --skip-validation        Skip live Model Armor API validation call
  -h, --help               Show this help message

Examples:
  ./bin/install-nandi.sh                 # Default: installs with hermetic .venv
  ./bin/install-nandi.sh --system        # Override: uses host system python3
  ./bin/install-nandi.sh --project-dir /path/to/my-project
  ./bin/install-nandi.sh -p .
  ./bin/install-nandi.sh --skip-auth
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-dir|--project)
      mkdir -p "$2"
      PROJECT_DIR="$(cd "$2" && pwd)"
      shift 2
      ;;
    --system)
      USE_VENV=false
      shift
      ;;
    --recreate-venv)
      RECREATE_VENV=true
      shift
      ;;
    --skip-auth)
      SKIP_AUTH=true
      shift
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      shift
      ;;
    -h|--help)
      print_usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      print_usage
      exit 1
      ;;
  esac
done

echo "============================================================"
echo " Nandi Installer (The Incorruptible Threshold Guardian)"
echo "============================================================"
echo "Repository Root Directory : ${REPO_ROOT}"
echo "Client Plugin Directory   : ${PLUGIN_ROOT}"
echo "GCP Server Infrastructure : ${GCP_ROOT}"
if [[ "${USE_VENV}" == "true" ]]; then
  echo "Python Runtime Mode  : Isolated Virtual Environment (${PLUGIN_ROOT}/.venv)"
else
  echo "Python Runtime Mode  : Host System Python3 (--system override)"
fi
if [[ -n "${PROJECT_DIR}" ]]; then
  TARGET_PLUGINS_DIR="${PROJECT_DIR}/_agents/plugins"
  DOT_TARGET_PLUGINS_DIR="${PROJECT_DIR}/.agents/plugins"
  echo "Installation Target  : Project Scoped (${PROJECT_DIR})"
else
  echo "Installation Target  : Global (${GLOBAL_TARGET_DIR_2}/nandi)"
fi
echo "============================================================"

# ------------------------------------------------------------------------------
# 1. Local Environment & Library Diagnostics
# ------------------------------------------------------------------------------
echo ""
echo "[Step 1/5] Local Environment & Library Diagnostics..."

# 1.1 Host Python runtime and version check (require >= 3.8)
if ! command -v python3 &> /dev/null; then
  echo "❌ Error: python3 is not installed or not available on PATH." >&2
  echo "   Nandi requires Python 3.8+ for hooks, CLI, and virtual environment provisioning." >&2
  exit 1
fi

HOST_PYTHON_BIN="$(command -v python3)"
HOST_PYTHON_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
HOST_PYTHON_MAJOR="$(python3 -c 'import sys; print(sys.version_info.major)')"
HOST_PYTHON_MINOR="$(python3 -c 'import sys; print(sys.version_info.minor)')"

if [[ "${HOST_PYTHON_MAJOR}" -lt 3 ]] || [[ "${HOST_PYTHON_MAJOR}" -eq 3 && "${HOST_PYTHON_MINOR}" -lt 8 ]]; then
  echo "❌ Error: Host Python version ${HOST_PYTHON_VER} is below minimum requirement (>= 3.8)." >&2
  echo "   Please upgrade Python 3 to version 3.8 or later." >&2
  exit 1
fi
echo "  ✓ Host python3 runtime verified: ${HOST_PYTHON_BIN} (v${HOST_PYTHON_VER})"

# 1.2 Virtual Environment Provisioning (Default) or System Override
VENV_DIR="${PLUGIN_ROOT}/.venv"
if [[ "${USE_VENV}" == "true" ]]; then
  if [[ "${RECREATE_VENV}" == "true" && -d "${VENV_DIR}" ]]; then
    echo "  Recreating virtual environment at ${VENV_DIR}..."
    rm -rf "${VENV_DIR}"
  fi

  if [[ ! -d "${VENV_DIR}" ]]; then
    echo "  Initializing isolated virtual environment at ${VENV_DIR}..."
    python3 -m venv "${VENV_DIR}"
    echo "  ✓ Virtual environment initialized: ${VENV_DIR}"
  else
    echo "  ✓ Existing virtual environment detected: ${VENV_DIR}"
  fi

  PYTHON_EXEC="${VENV_DIR}/bin/python3"
  if [[ ! -x "${PYTHON_EXEC}" ]]; then
    echo "❌ Error: Virtual environment python binary not executable: ${PYTHON_EXEC}" >&2
    exit 1
  fi

  # Attempt installing optional acceleration packages in .venv if pip is available
  if [[ -x "${VENV_DIR}/bin/pip" ]]; then
    echo "  Checking optional acceleration packages in .venv (google-auth, pyyaml)..."
    "${VENV_DIR}/bin/pip" install --quiet google-auth pyyaml 2>/dev/null || true
  fi
else
  PYTHON_EXEC="${HOST_PYTHON_BIN}"
  echo "  ℹ Using host system python3 (--system override active): ${PYTHON_EXEC}"
fi

# 1.3 Core standard library modules check using target PYTHON_EXEC
"${PYTHON_EXEC}" - "${PLUGIN_ROOT}" <<'PY'
import sys
required_modules = [
    "dataclasses",
    "hashlib",
    "json",
    "os",
    "re",
    "subprocess",
    "sys",
    "time",
    "typing",
    "urllib.request",
    "urllib.error",
]
missing = []
for mod in required_modules:
    try:
        __import__(mod)
    except ImportError:
        missing.append(mod)

if missing:
    print(f"❌ Missing requisite Python modules in runtime: {', '.join(missing)}", file=sys.stderr)
    print("   Please ensure your Python runtime includes standard library modules.", file=sys.stderr)
    sys.exit(1)
print(f"  ✓ Requisite Python standard libraries verified ({len(required_modules)} modules) in {sys.executable}")
PY

# 1.4 Optional acceleration & configuration packages check in PYTHON_EXEC
"${PYTHON_EXEC}" - <<'PY'
try:
    import google.auth
    import google.auth.transport.requests
    print("  ✓ google-auth detected in runtime (high-performance in-process ADC token acquisition enabled)")
except ImportError:
    print("  ℹ google-auth not installed in runtime (falling back to gcloud CLI token extraction; lower hook latency with 'pip install google-auth')")

try:
    import yaml
    print("  ✓ pyyaml detected in runtime (YAML configuration parsing enabled)")
except ImportError:
    print("  ℹ pyyaml not installed in runtime (standard JSON fallback configuration parser active)")
PY

# 1.5 Google Cloud SDK (gcloud CLI) verification
if ! command -v gcloud &> /dev/null; then
  echo "❌ Error: Google Cloud SDK ('gcloud' CLI) is not installed or not on PATH." >&2
  echo "   Google Cloud Model Armor requires gcloud for authentication, ADC tokens, and project management." >&2
  echo "   Please install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install" >&2
  exit 1
fi

GCLOUD_BIN="$(command -v gcloud)"
GCLOUD_VER="$(gcloud --version 2>/dev/null | head -n 1)"
GCLOUD_ACCOUNT="$(gcloud config get-value account 2>/dev/null || echo "(none)")"
GCLOUD_PROJECT="$(gcloud config get-value project 2>/dev/null || echo "(none)")"
echo "  ✓ gcloud CLI verified: ${GCLOUD_BIN} (${GCLOUD_VER})"
echo "    Active gcloud Account : ${GCLOUD_ACCOUNT}"
echo "    Active gcloud Project : ${GCLOUD_PROJECT}"

# 1.6 Local repository file & hook integrity check
REQUIRED_FILES=(
  "plugin.json"
  "hooks.json"
  "config/config.yaml"
  "config/pii_patterns.json"
  "config/model_armor_policy.json"
  "src/hooks/hook_base.py"
  "src/hooks/pii_hook.py"
  "src/hooks/model_armor_hook.py"
  "src/hooks/combined_guard_hook.py"
  "src/cli/grc_admin.py"
  "src/model_armor/client.py"
  "src/model_armor/policy_evaluator.py"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "${PLUGIN_ROOT}/${file}" ]]; then
    echo "❌ Missing required client plugin file: ${file}" >&2
    echo "   Please verify that your git repository clone is complete and intact." >&2
    exit 1
  fi
done

GCP_REQUIRED_FILES=(
  "terraform/main.tf"
  "terraform/variables.tf"
  "terraform/outputs.tf"
  "generated_model_armor_template.json"
)

for file in "${GCP_REQUIRED_FILES[@]}"; do
  if [[ ! -f "${GCP_ROOT}/${file}" ]]; then
    echo "❌ Missing required GCP server infrastructure file: ${file}" >&2
    echo "   Please verify that the GCP server directory is complete and intact." >&2
    exit 1
  fi
done
echo "  ✓ Local client and GCP repository integrity verified"

# ------------------------------------------------------------------------------
# 2. Google Cloud Authentication ('gcloud auth application-default login')
# ------------------------------------------------------------------------------
echo ""
echo "[Step 2/5] Google Cloud Authentication (Application Default Credentials)..."

if [[ "${SKIP_AUTH}" == "true" ]]; then
  echo "  ✓ Skipping interactive 'gcloud auth application-default login' (--skip-auth specified)."
else
  echo "  Running 'gcloud auth application-default login' for Model Armor API access..."
  gcloud auth application-default login
  echo "  ✓ Google Cloud Application Default Credentials configured successfully."
fi

# Cache access token in environment for fast Python API calls if available
if [[ -z "${GOOGLE_OAUTH_ACCESS_TOKEN:-}" && -z "${GCP_ACCESS_TOKEN:-}" ]]; then
  TOKEN="$(gcloud auth application-default print-access-token 2>/dev/null || gcloud auth print-access-token 2>/dev/null || true)"
  if [[ -n "${TOKEN}" ]]; then
    export GOOGLE_OAUTH_ACCESS_TOKEN="${TOKEN}"
  fi
fi

# ------------------------------------------------------------------------------
# 3. Google Cloud Project & Model Armor Template Diagnostics
# ------------------------------------------------------------------------------
echo ""
echo "[Step 3/5] Google Cloud Project & Model Armor Template Diagnostics..."

if [[ "${SKIP_VALIDATION}" == "true" ]]; then
  echo "  ✓ Skipping Google Cloud project & Model Armor validation (--skip-validation specified)."
else
  "${PYTHON_EXEC}" - "${PLUGIN_ROOT}" "${GCP_ROOT}" <<'PY'
import json
import os
import socket
import sys

plugin_root = sys.argv[1]
gcp_root = sys.argv[2]
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from src.model_armor.client import ModelArmorClient

client = ModelArmorClient()

print(f"  Target GCP Project ID : {client.project_id}")
print(f"  Target GCP Location   : {client.location}")
print(f"  Target Template ID    : {client.template_id}")

# 3.1 Regional Endpoint reachability check
endpoint_host = (
    client.endpoint
    if client.endpoint
    else ("modelarmor.googleapis.com" if client.location == "global" else f"modelarmor.{client.location}.rep.googleapis.com")
)
print(f"  Regional REP Endpoint : {endpoint_host}")

try:
    ip = socket.gethostbyname(endpoint_host)
    print(f"  ✓ DNS reachability verified: {endpoint_host} -> {ip}")
except Exception as e:
    print(f"  ⚠️ Warning: DNS resolution for {endpoint_host} failed ({e}). Proceeding to API check...")

# 3.2 Model Armor Template Diagnostics via get_template()
print(f"\n  Inspecting Model Armor template 'projects/{client.project_id}/locations/{client.location}/templates/{client.template_id}'...")

template_res = client.get_template()

if not template_res.get("success"):
    status_code = template_res.get("status_code", 0)
    error_msg = template_res.get("error_message", "Unknown error")

    print(f"\n❌ GCP Project Model Armor Template Diagnostic FAILED (HTTP {status_code}):")
    print(f"   Resource: {template_res.get('resource_name')}")
    print(f"   Error   : {error_msg}")

    if status_code == 404:
        print("\n[DIAGNOSTIC] Model Armor Template NOT FOUND in GCP Project.")
        print(f"  The template '{client.template_id}' does not exist in projects/{client.project_id}/locations/{client.location}.")
        print("\n  Remediation Option A (Automated Terraform):")
        print(f"    cd {gcp_root}/terraform")
        print("    cp terraform.tfvars.example terraform.tfvars")
        print(f"    # Ensure project_id=\"{client.project_id}\" and region=\"{client.location}\" are set")
        print("    terraform init && terraform apply")
        print("\n  Remediation Option B (Direct REST / gcloud API):")
        print(f"    curl -X POST \\")
        print(f"      -H \"Authorization: Bearer $(gcloud auth print-access-token)\" \\")
        print(f"      -H \"Content-Type: application/json; charset=utf-8\" \\")
        print(f"      -H \"X-Goog-User-Project: {client.project_id}\" \\")
        print(f"      \"https://{endpoint_host}/v1/projects/{client.project_id}/locations/{client.location}/templates?templateId={client.template_id}\" \\")
        print(f"      -d @{gcp_root}/generated_model_armor_template.json")
        print(f"\n  Refer to {gcp_root}/MODEL_ARMOR_SETUP.md for complete configuration details.")
    elif status_code == 403:
        print("\n[DIAGNOSTIC] PERMISSION DENIED accessing Model Armor in GCP Project.")
        print(f"  The authenticated identity lacks required IAM permissions on project '{client.project_id}'.")
        print("\n  Remediation Commands:")
        print(f"    1. Enable Model Armor API:")
        print(f"       gcloud services enable modelarmor.googleapis.com --project={client.project_id}")
        print(f"    2. Grant Model Armor User & Viewer roles to your user:")
        print(f"       gcloud projects add-iam-policy-binding {client.project_id} \\")
        print(f"         --member=\"user:$(gcloud config get-value account)\" \\")
        print(f"         --role=\"roles/modelarmor.user\"")
        print(f"       gcloud projects add-iam-policy-binding {client.project_id} \\")
        print(f"         --member=\"user:$(gcloud config get-value account)\" \\")
        print(f"         --role=\"roles/modelarmor.viewer\"")
    elif status_code == 401:
        print("\n[DIAGNOSTIC] AUTHENTICATION FAILED obtaining GCP OAuth2 Token.")
        print("  Please re-run 'gcloud auth application-default login' or export GOOGLE_OAUTH_ACCESS_TOKEN.")
    else:
        print("\n[DIAGNOSTIC] Unexpected Model Armor API error.")
        print("  Please check network access, proxy settings, or GCP service health.")

    print("\nInstallation aborted due to failed GCP project prerequisites.")
    sys.exit(1)

template_data = template_res.get("template", {})
print(f"  ✓ Model Armor Template verified exists!")
print(f"    Resource Name : {template_data.get('name', template_res.get('resource_name'))}")
if "updateTime" in template_data:
    print(f"    Last Updated  : {template_data.get('updateTime')}")

# Inspect and display configured safety filters
filter_cfg = template_data.get("filterConfig", template_data.get("filter_config", {}))

pi_cfg = filter_cfg.get("piAndJailbreakFilterConfig") or filter_cfg.get("pi_and_jailbreak_filter_settings")
if pi_cfg:
    enforcement = pi_cfg.get("filterEnforcement") or pi_cfg.get("filter_enforcement", "ENABLED")
    conf = pi_cfg.get("confidenceLevel") or pi_cfg.get("confidence_level", "DEFAULT")
    print(f"    ✓ Prompt Injection & Jailbreak Filter: {enforcement} (Confidence: {conf})")
else:
    print(f"    ℹ Prompt Injection & Jailbreak Filter: (Not configured in template)")

rai_cfg = filter_cfg.get("raiFilterConfig") or filter_cfg.get("rai_settings")
if rai_cfg:
    print(f"    ✓ Responsible AI (RAI) Content Filters: ACTIVE")
else:
    print(f"    ℹ Responsible AI (RAI) Content Filters: (Not configured in template)")

uri_cfg = filter_cfg.get("maliciousUriFilterConfig") or filter_cfg.get("malicious_uri_settings")
if uri_cfg:
    print(f"    ✓ Malicious URI Filter: ACTIVE")
else:
    print(f"    ℹ Malicious URI Filter: (Not configured or not supported in this region)")

tmpl_meta = template_data.get("templateMetadata", template_data.get("template_metadata", {}))
multi_lang = filter_cfg.get("multiLanguageConfig") or tmpl_meta.get("multi_language_config")
if multi_lang:
    print(f"    ✓ Multi-Language Detection: ENABLED")

# 3.3 Live Prompt Sanitization Validation Call
print(f"\n  Executing sample Model Armor prompt sanitization call...")
sample_prompt = "Verify Google Cloud Model Armor connectivity and FSI template guardrails."
resp = client.sanitize_user_prompt(sample_prompt)

if not resp.success:
    print(f"\n❌ Live Model Armor Prompt Sanitization FAILED:")
    print(f"   Error: {resp.error_message}")
    print(f"   Status Code: {resp.status_code}")
    print("\nInstallation aborted. Live Model Armor call did not succeed.")
    sys.exit(1)

print(f"  ✓ Live Model Armor API Call Succeeded!")
print(f"    Invocation Result : {resp.invocation_result}")
print(f"    Filter Match State: {resp.filter_match_state}")
print(f"    Response Latency  : {resp.latency_ms}ms")
PY
fi

# ------------------------------------------------------------------------------
# 4. Make Hook Entrypoints Executable & Run Test Suite
# ------------------------------------------------------------------------------
echo ""
echo "[Step 4/5] Running Test Suite..."

chmod +x "${PLUGIN_ROOT}"/src/hooks/*.py "${PLUGIN_ROOT}/src/cli/grc_admin.py" "${SCRIPT_DIR}/install-nandi.sh"
echo "✓ Made hook entrypoints and CLI executable"

"${PYTHON_EXEC}" "${REPO_ROOT}/tests/run_all_tests.py"
echo "✓ All 31 unit tests passed successfully"

# Dynamically update hooks.json with absolute path and exact python interpreter
"${PYTHON_EXEC}" - "${PLUGIN_ROOT}/hooks.json" "${PLUGIN_ROOT}" "${PYTHON_EXEC}" <<'PY'
import json, sys

hook_path, plugin_root, python_exec = sys.argv[1], sys.argv[2], sys.argv[3]
with open(hook_path, "r") as f:
    data = json.load(f)

for guard_name, guard_cfg in data.items():
    if not isinstance(guard_cfg, dict):
        continue
    for stage in ["PreInvocation", "PreToolUse"]:
        items = guard_cfg.get(stage, [])
        for item in items:
            if isinstance(item, dict):
                if "command" in item and "/src/hooks/" in item["command"]:
                    hook_file = item["command"].split("/src/hooks/")[-1].split()[0]
                    item["command"] = f"{python_exec} {plugin_root}/src/hooks/{hook_file}"
                for sub_hook in item.get("hooks", []):
                    if isinstance(sub_hook, dict) and "command" in sub_hook and "/src/hooks/" in sub_hook["command"]:
                        hook_file = sub_hook["command"].split("/src/hooks/")[-1].split()[0]
                        sub_hook["command"] = f"{python_exec} {plugin_root}/src/hooks/{hook_file}"

with open(hook_path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
echo "✓ Configured hooks.json to execute using ${PYTHON_EXEC}"

# ------------------------------------------------------------------------------
# 5. Install Nandi Plugin Installables
# ------------------------------------------------------------------------------
echo ""
echo "[Step 5/5] Installing Nandi Plugin Installables..."

if [[ -n "${PROJECT_DIR}" ]]; then
  # Remove global symlinks if present so plugin is strictly scoped to this project alone
  for global_link in "${GLOBAL_TARGET_DIR_1}/nandi" \
                     "${GLOBAL_TARGET_DIR_1}/antigravity-fsi-india-guard" \
                     "${GLOBAL_TARGET_DIR_1}/grc-plugin" \
                     "${GLOBAL_TARGET_DIR_2}/nandi" \
                     "${GLOBAL_TARGET_DIR_2}/antigravity-fsi-india-guard" \
                     "${GLOBAL_TARGET_DIR_2}/grc-plugin"; do
    if [[ -L "${global_link}" || -e "${global_link}" ]]; then
      rm -f "${global_link}"
      echo "✓ Removed global plugin link (${global_link}) to isolate within project"
    fi
  done

  # Create project customization roots
  mkdir -p "${TARGET_PLUGINS_DIR}" "${DOT_TARGET_PLUGINS_DIR}" "${PROJECT_DIR}/.antigravity/plugins"
  rm -f "${TARGET_PLUGINS_DIR}/nandi" "${TARGET_PLUGINS_DIR}/grc-plugin" "${TARGET_PLUGINS_DIR}/antigravity-fsi-india-guard"
  ln -s "${PLUGIN_ROOT}" "${TARGET_PLUGINS_DIR}/nandi"
  echo "✓ Symlinked plugin to project root: ${TARGET_PLUGINS_DIR}/nandi"

  rm -f "${DOT_TARGET_PLUGINS_DIR}/nandi" "${DOT_TARGET_PLUGINS_DIR}/grc-plugin" "${DOT_TARGET_PLUGINS_DIR}/antigravity-fsi-india-guard"
  ln -s "${PLUGIN_ROOT}" "${DOT_TARGET_PLUGINS_DIR}/nandi"
  echo "✓ Symlinked plugin to project root: ${DOT_TARGET_PLUGINS_DIR}/nandi"

  rm -f "${PROJECT_DIR}/.antigravity/plugins/nandi" "${PROJECT_DIR}/.antigravity/plugins/antigravity-fsi-india-guard"
  ln -s "${PLUGIN_ROOT}" "${PROJECT_DIR}/.antigravity/plugins/nandi"

  # Symlink hooks.json directly into project customization roots so lifecycle hooks fire for this project
  rm -f "${PROJECT_DIR}/_agents/hooks.json" "${PROJECT_DIR}/.agents/hooks.json" "${PROJECT_DIR}/.antigravity/hooks.json"
  ln -s "${PLUGIN_ROOT}/hooks.json" "${PROJECT_DIR}/_agents/hooks.json"
  ln -s "${PLUGIN_ROOT}/hooks.json" "${PROJECT_DIR}/.agents/hooks.json"
  ln -s "${PLUGIN_ROOT}/hooks.json" "${PROJECT_DIR}/.antigravity/hooks.json"
  echo "✓ Symlinked hooks.json to project customization root: ${PROJECT_DIR}/_agents/hooks.json"

  # Update plugins.json safely using python to preserve existing entries
  "${PYTHON_EXEC}" - "${PROJECT_DIR}/_agents/plugins.json" "${PLUGIN_ROOT}" <<'PY'
import json, os, sys
path, plugin_dir = sys.argv[1], sys.argv[2]
data = {"entries": []}
if os.path.exists(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        pass
entries = data.get("entries", [])
if not any(e.get("path") == plugin_dir for e in entries):
    entries.append({"path": plugin_dir})
data["entries"] = entries
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
  cp "${PROJECT_DIR}/_agents/plugins.json" "${PROJECT_DIR}/.agents/plugins.json"
  echo "✓ Configured project plugins.json at ${PROJECT_DIR}/_agents/plugins.json"
else
  mkdir -p "${GLOBAL_TARGET_DIR_2}"
  rm -f "${GLOBAL_TARGET_DIR_2}/nandi" "${GLOBAL_TARGET_DIR_2}/antigravity-fsi-india-guard"
  ln -s "${PLUGIN_ROOT}" "${GLOBAL_TARGET_DIR_2}/nandi"
  echo "✓ Symlinked plugin globally to: ${GLOBAL_TARGET_DIR_2}/nandi"
fi

echo ""
echo "============================================================"
if [[ -n "${PROJECT_DIR}" ]]; then
  echo "🎉 Successfully installed Nandi (Project Scoped Only)!"
  echo "Project Directory: ${PROJECT_DIR}"
else
  echo "🎉 Successfully installed Nandi (Globally)!"
fi
echo "Plugin is active and discoverable by Antigravity."
echo "============================================================"
