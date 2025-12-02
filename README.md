
# InSARchitect
InSARChitect is an orchestrator that integrates ISCE2, MiaplPy, and MintPy within a cluster-based architecture to streamline and automate InSAR processing workflows.


## Installation

Run the following script:

```bash
bash scripts/install.sh
```

This will install `pixi`, download the required packages, and clone and install
repositories such as `ISCE2`, `MintPy`, and `MiaplPy`.

Be sure you have the correct access permissions for these private repositories.

Then, activate a shell in the environment
```bash
pixi shell
```

To check the installation integrity, run the pixi test

```bash
pixi run test
```

Run the program

```bash
pixi run insarchitect <command> <template.toml>
```

Example

```bash
pixi run insarchitect download template.example.toml
```
