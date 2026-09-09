#!/usr/bin/env bash
# ==============================================================================
# Nandi Installer
# Installs and validates Nandi for Google Antigravity.
# Supports global installation or project-scoped installation (-p / --project-dir).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GLOBAL_TARGET_DIR_1="${HOME}/.gemini/antigravity/plugins"
GLOBAL_TARGET_DIR_2="${HOME}/.gemini/config/plugins"

PROJECT_DIR=""

print_usage() {
  cat <<EOF
Usage: ./install.sh [OPTIONS]

Options:
  -p, --project-dir DIR    Install plugin scoped to a specific project alone (project-scoped)
  -h, --help               Show this help message

Examples:
  ./install.sh --project-dir /path/to/my-project
  ./install.sh -p .
  ./install.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project-dir|--project)
      PROJECT_DIR="$(cd "$2" && pwd)"
      shift 2
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

if [[ -n "${PROJECT_DIR}" ]]; then
  TARGET_PLUGINS_DIR="${PROJECT_DIR}/_agents/plugins"
  DOT_TARGET_PLUGINS_DIR="${PROJECT_DIR}/.agents/plugins"
  echo "============================================================"
  echo "Installing Nandi (Project Scoped Only)"
  echo "  Source Directory : ${SCRIPT_DIR}"
  echo "  Project Root     : ${PROJECT_DIR}"
  echo "  Target Directory : ${TARGET_PLUGINS_DIR}/nandi"
  echo "============================================================"
else
  echo "============================================================"
  echo "Installing Nandi (Global)"
  echo "  Source Directory : ${SCRIPT_DIR}"
  echo "  Target Directory : ${GLOBAL_TARGET_DIR_2}/nandi"
  echo "============================================================"
fi

# 1. Check Python 3 requirement
if ! command -v python3 &> /dev/null; then
  echo "Error: python3 is required for GRC Plugin hooks and CLI."
  exit 1
fi
echo "✓ python3 verified: $(python3 --version)"

# 2. Make hook entrypoints and CLI executable
chmod +x "${SCRIPT_DIR}"/src/hooks/*.py "${SCRIPT_DIR}/src/cli/grc_admin.py"
echo "✓ Made src/hooks/*.py and src/cli/grc_admin.py executable"

# 3. Run unit tests
echo "Running GRC Plugin unit test suite..."
python3 "${SCRIPT_DIR}/tests/run_all_tests.py"
echo "✓ All 27 unit tests passed successfully"

# 4. Install plugin (Project-Scoped vs Global)
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
  ln -s "${SCRIPT_DIR}" "${TARGET_PLUGINS_DIR}/nandi"
  echo "✓ Symlinked plugin to project root: ${TARGET_PLUGINS_DIR}/nandi"

  rm -f "${DOT_TARGET_PLUGINS_DIR}/nandi" "${DOT_TARGET_PLUGINS_DIR}/grc-plugin" "${DOT_TARGET_PLUGINS_DIR}/antigravity-fsi-india-guard"
  ln -s "${SCRIPT_DIR}" "${DOT_TARGET_PLUGINS_DIR}/nandi"
  echo "✓ Symlinked plugin to project root: ${DOT_TARGET_PLUGINS_DIR}/nandi"

  rm -f "${PROJECT_DIR}/.antigravity/plugins/nandi" "${PROJECT_DIR}/.antigravity/plugins/antigravity-fsi-india-guard"
  ln -s "${SCRIPT_DIR}" "${PROJECT_DIR}/.antigravity/plugins/nandi"

  # Symlink hooks.json directly into project customization roots so lifecycle hooks fire for this project
  rm -f "${PROJECT_DIR}/_agents/hooks.json" "${PROJECT_DIR}/.agents/hooks.json" "${PROJECT_DIR}/.antigravity/hooks.json"
  ln -s "${SCRIPT_DIR}/hooks.json" "${PROJECT_DIR}/_agents/hooks.json"
  ln -s "${SCRIPT_DIR}/hooks.json" "${PROJECT_DIR}/.agents/hooks.json"
  ln -s "${SCRIPT_DIR}/hooks.json" "${PROJECT_DIR}/.antigravity/hooks.json"
  echo "✓ Symlinked hooks.json to project customization root: ${PROJECT_DIR}/_agents/hooks.json"

  # Update plugins.json safely using python to preserve existing entries
  python3 - "${PROJECT_DIR}/_agents/plugins.json" "${SCRIPT_DIR}" <<'PY'
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
  ln -s "${SCRIPT_DIR}" "${GLOBAL_TARGET_DIR_2}/nandi"
  echo "✓ Symlinked plugin globally to: ${GLOBAL_TARGET_DIR_2}/nandi"
fi

echo ""
echo "============================================================"
if [[ -n "${PROJECT_DIR}" ]]; then
  echo "Successfully installed Nandi (Project Scoped Only)!"
  echo "Project Directory: ${PROJECT_DIR}"
else
  echo "Successfully installed Nandi (Globally)!"
fi
echo "Plugin is active and discoverable by Antigravity."
echo "============================================================"
