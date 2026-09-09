#!/usr/bin/env bash
# ==============================================================================
# Nandi Installer
# The Incorruptible Threshold Guardian for Google Antigravity.
#
# Execution Flow:
#  1. Verify Prerequisites (Python 3 & gcloud CLI)
#  2. Google Cloud Authentication ('gcloud auth login')
#  3. Validate Model Armor API with a live sample prompt
#  4. Execute Unit Test Suite (27 tests)
#  5. Install Nandi plugin installables (Global or Project-Scoped)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

GLOBAL_TARGET_DIR_1="${HOME}/.gemini/antigravity/plugins"
GLOBAL_TARGET_DIR_2="${HOME}/.gemini/config/plugins"

PROJECT_DIR=""
SKIP_AUTH=false
SKIP_VALIDATION=false

print_usage() {
  cat <<EOF
Usage: ./bin/install-nandi.sh [OPTIONS]

Options:
  -p, --project-dir DIR    Install plugin scoped to a specific project alone (project-scoped)
  --skip-auth              Skip interactive 'gcloud auth login' (e.g. if already logged in)
  --skip-validation        Skip live Model Armor API validation call
  -h, --help               Show this help message

Examples:
  ./bin/install-nandi.sh
  ./bin/install-nandi.sh --project-dir /path/to/my-project
  ./bin/install-nandi.sh -p .
  ./bin/install-nandi.sh --skip-auth
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-dir|--project)
      PROJECT_DIR="$(cd "$2" && pwd)"
      shift 2
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
echo "Plugin Root Directory: ${PLUGIN_ROOT}"
if [[ -n "${PROJECT_DIR}" ]]; then
  TARGET_PLUGINS_DIR="${PROJECT_DIR}/_agents/plugins"
  DOT_TARGET_PLUGINS_DIR="${PROJECT_DIR}/.agents/plugins"
  echo "Installation Target  : Project Scoped (${PROJECT_DIR})"
else
  echo "Installation Target  : Global (${GLOBAL_TARGET_DIR_2}/nandi)"
fi
echo "============================================================"

# ------------------------------------------------------------------------------
# 1. Check Prerequisites (Python 3 & gcloud CLI)
# ------------------------------------------------------------------------------
echo ""
echo "[Step 1/5] Checking Prerequisites..."

if ! command -v python3 &> /dev/null; then
  echo "❌ Error: python3 is required for Nandi hooks and CLI." >&2
  exit 1
fi
echo "✓ python3 verified: $(python3 --version)"

if ! command -v gcloud &> /dev/null; then
  echo "❌ Error: Google Cloud SDK ('gcloud' CLI) is not installed on this device." >&2
  echo "Google Cloud Model Armor requires the gcloud CLI for authentication and API validation." >&2
  echo "Please install gcloud from https://cloud.google.com/sdk/docs/install and try again." >&2
  exit 1
fi
echo "✓ gcloud CLI verified: $(gcloud --version 2>/dev/null | head -n 1)"

# ------------------------------------------------------------------------------
# 2. Google Cloud Authentication ('gcloud auth login')
# ------------------------------------------------------------------------------
echo ""
echo "[Step 2/5] Google Cloud Authentication..."

if [[ "${SKIP_AUTH}" == "true" ]]; then
  echo "✓ Skipping 'gcloud auth login' (--skip-auth specified)."
else
  echo "Running 'gcloud auth login' for Model Armor API access..."
  gcloud auth login
  echo "✓ Google Cloud authentication completed successfully."
fi

# Cache access token in environment for fast Python API calls if available
if [[ -z "${GOOGLE_OAUTH_ACCESS_TOKEN:-}" && -z "${GCP_ACCESS_TOKEN:-}" ]]; then
  TOKEN="$(gcloud auth print-access-token 2>/dev/null || true)"
  if [[ -n "${TOKEN}" ]]; then
    export GOOGLE_OAUTH_ACCESS_TOKEN="${TOKEN}"
  fi
fi

# ------------------------------------------------------------------------------
# 3. Live Model Armor API Validation Call from End-User Device
# ------------------------------------------------------------------------------
echo ""
echo "[Step 3/5] Validating Model Armor Connection from Device..."

if [[ "${SKIP_VALIDATION}" == "true" ]]; then
  echo "✓ Skipping live Model Armor API validation (--skip-validation specified)."
else
  echo "Executing sample Model Armor validation call..."
  python3 - "${PLUGIN_ROOT}" <<'PY'
import sys, os

plugin_root = sys.argv[1]
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from src.model_armor.client import ModelArmorClient

client = ModelArmorClient()

sample_prompt = "Verify Google Cloud Model Armor connectivity and FSI template guardrails."
print(f"  Target Project : {client.project_id}")
print(f"  Location       : {client.location}")
print(f"  Template ID    : {client.template_id}")
print(f"  Sample Prompt  : \"{sample_prompt}\"")

resp = client.sanitize_user_prompt(sample_prompt)
if not resp.success:
    print(f"\n❌ Model Armor API Validation FAILED:")
    print(f"   Error: {resp.error_message}")
    print(f"   Status Code: {resp.status_code}")
    print("\nInstallation aborted. Please ensure that:")
    print("1. You have run 'gcloud auth login' with permissions to project 'stratosphere-461622'")
    print("2. The Model Armor template exists in region 'asia-south1'")
    print("3. Your device has network access to modelarmor.asia-south1.rep.googleapis.com")
    sys.exit(1)

print(f"✓ Model Armor API Call Succeeded!")
print(f"   Invocation Result : {resp.invocation_result}")
print(f"   Filter Match State: {resp.filter_match_state}")
print(f"   Latency           : {resp.latency_ms}ms")
PY
fi

# ------------------------------------------------------------------------------
# 4. Make Hook Entrypoints Executable & Run Test Suite
# ------------------------------------------------------------------------------
echo ""
echo "[Step 4/5] Running Test Suite..."

chmod +x "${PLUGIN_ROOT}"/src/hooks/*.py "${PLUGIN_ROOT}/src/cli/grc_admin.py" "${SCRIPT_DIR}/install-nandi.sh"
echo "✓ Made hook entrypoints and CLI executable"

python3 "${PLUGIN_ROOT}/tests/run_all_tests.py"
echo "✓ All 27 unit tests passed successfully"

# Dynamically update hooks.json with absolute path to this clone's hook entrypoints
python3 - "${PLUGIN_ROOT}/hooks.json" "${PLUGIN_ROOT}" <<'PY'
import sys, re
hook_path, plugin_root = sys.argv[1], sys.argv[2]
with open(hook_path, "r") as f:
    content = f.read()
content = re.sub(r'python3\s+.*?/src/hooks/', f'python3 {plugin_root}/src/hooks/', content)
with open(hook_path, "w") as f:
    f.write(content)
PY

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
  python3 - "${PROJECT_DIR}/_agents/plugins.json" "${PLUGIN_ROOT}" <<'PY'
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
