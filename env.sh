#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOLS_DIR="${PROJECT_ROOT}/tools"

export MINTPY_HOME="${TOOLS_DIR}/MintPy"
export MIAPLPY_HOME="${TOOLS_DIR}/MiaplPy"
export ISCE_HOME="${TOOLS_DIR}/isce2"
export INSARMAPS_SCRIPTS_HOME="${TOOLS_DIR}/insarmaps-scripts"

[ -d "${MINTPY_HOME}" ] && export PYTHONPATH="${MINTPY_HOME}:${PYTHONPATH}"
[ -d "${MIAPLPY_HOME}" ] && export PYTHONPATH="${MIAPLPY_HOME}:${PYTHONPATH}"
[ -d "${ISCE_HOME}" ] && export PYTHONPATH="${ISCE_HOME}:${PYTHONPATH}"

[ -d "${MINTPY_HOME}/src/mintpy" ] && export PATH="${MINTPY_HOME}/src/mintpy:${PATH}"
[ -d "${MIAPLPY_HOME}/src/miaplpy" ] && export PATH="${MIAPLPY_HOME}/src/miaplpy:${PATH}"

export PATH="${INSARMAPS_SCRIPTS_HOME}:${PATH}"

echo "InSARchitect environment variables set"
