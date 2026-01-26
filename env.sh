#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}" && pwd)"
TOOLS_DIR="${PROJECT_ROOT}/tools"

export MINTPY_HOME="${TOOLS_DIR}/MintPy"
export MIAPLPY_HOME="${TOOLS_DIR}/MiaplPy"
export ISCE_HOME="${TOOLS_DIR}/isce2"
export INSARMAPS_SCRIPTS_HOME="${TOOLS_DIR}/insarmaps-scripts"
export ISCE_STACK="${TOOLS_DIR}/isce2/contrib/stack"

export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

[ -d "${MINTPY_HOME}" ] && export PYTHONPATH="${MINTPY_HOME}:${PYTHONPATH}"
[ -d "${MIAPLPY_HOME}" ] && export PYTHONPATH="${MIAPLPY_HOME}:${PYTHONPATH}"
[ -d "${ISCE_HOME}" ] && export PYTHONPATH="${ISCE_HOME}:${PYTHONPATH}"
[ -d "${ISCE_STACK}" ] && export PYTHONPATH="${ISCE_STACK}:${PYTHONPATH}"

[ -d "${MINTPY_HOME}/src/mintpy" ] && export PATH="${MINTPY_HOME}/src/mintpy:${PATH}"
[ -d "${MIAPLPY_HOME}/src/miaplpy" ] && export PATH="${MIAPLPY_HOME}/src/miaplpy:${PATH}"

[ -d "${ISCE_STACK}/topsStack" ] && export PATH="${ISCE_STACK}/topsStack:${PATH}"
[ -d "${ISCE_STACK}" ] && export PYTHONPATH="${ISCE_STACK}:${PYTHONPATH}"

export PATH="${INSARMAPS_SCRIPTS_HOME}:${PATH}"

echo "InSARchitect environment variables set"
