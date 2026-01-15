
# InSARchitect
InSARChitect is an orchestrator that integrates ISCE2, MiaplPy, and MintPy within a cluster-based architecture to streamline and automate InSAR processing workflows.


## Installation

Run the following script:

```bash
bash scripts/install.sh
```

This will install `pixi`, download the required packages, and clone and install
repositories such as `ISCE2`, `MintPy`, and `MiaplPy`.

IMPORTANT: Be sure you have the correct access permissions for these private repositories.

After the installation process, open a new bash session

```bash
bash
```

Then, activate the environment
```bash
insarchitect.load
```

Run the program

```bash
insarchitect <command> <template.toml>
```

Example

```bash
insarchitect download templates/galapagos.toml
```
