#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TOOLS_DIR="${PROJECT_ROOT}/tools"

export MINTPY_HOME="${TOOLS_DIR}/MintPy"
export MIAPLPY_HOME="${TOOLS_DIR}/MiaplPy"
export ISCE_HOME="${TOOLS_DIR}/isce2"

[ -d "${MINTPY_HOME}" ] && export PYTHONPATH="${MINTPY_HOME}:${PYTHONPATH}"
[ -d "${MIAPLPY_HOME}" ] && export PYTHONPATH="${MIAPLPY_HOME}:${PYTHONPATH}"
[ -d "${ISCE_HOME}" ] && export PYTHONPATH="${ISCE_HOME}:${PYTHONPATH}"

[ -d "${MINTPY_HOME}/src/mintpy" ] && export PATH="${MINTPY_HOME}/src/mintpy:${PATH}"
[ -d "${MIAPLPY_HOME}/src/miaplpy" ] && export PATH="${MIAPLPY_HOME}/src/miaplpy:${PATH}"

echo "InSARchitect environment variables set"
echo "  MINTPY_HOME: ${MINTPY_HOME}"
echo "  MIAPLPY_HOME: ${MIAPLPY_HOME}"
echo "  ISCE_HOME: ${ISCE_HOME}"

