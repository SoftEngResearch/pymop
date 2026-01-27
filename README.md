# PyMOP: A Runtime Verification Tool for Python

## Projects and data
You can find our 847 projects [here](data/results_metadata.csv), and you can find all the projects' data in this [directory](data).

## System Requirements

PyMOP requires the following components to be installed on your system:

- **Python**: Version 3.12 or later
- **Java**: Version 20 or later
- **Docker**: (optional, but recommended for simplified setup)

<!--
## Tutorial

This tutorial demonstrates how to use PyMOP to perform runtime verification on an open-source Python project using Ubuntu Linux. The tutorial walks through installation, setup, and running PyMOP on a real-world example.

### Setup PyMOP with Docker

This is the recommended way to setup PyMOP as it is the easiest way to get started and avoid any dependency issues.

If you don't have Docker installed, follow the instructions [here](https://docs.docker.com/get-docker/) to install Docker.

There is currently one way to run PyMOP with Docker:

1. Building the Docker image from source

a. Navigate to the `docker_files/demo` folder from the root directory:

```bash
cd docker_files/demo
```

b. Build the Docker image using:

```bash
docker build -t pymop .
```

This will build the Docker image and tag it as `pymop`.

c. Run the Docker container using:

```bash
docker run -it pymop
```

This will start the Docker container and should include the PyMOP repository and all the dependencies.

d. Activate the PyMOP virtual environment:

The PyMOP docker image should have already install PyMOP in the `pymop-venv` virtual environment. You can activate it by running:

```bash
source pymop-venv/bin/activate
```

This will activate the PyMOP virtual environment and you can now use PyMOP on any project you want.

### Run PyMOP on a open-source project

This section will guide you through running PyMOP on a open-source project. We'll use the `gdipak` project as an example.

To run PyMOP on a open-source project, you need to follow these steps:

1. Set Up Test Project
```bash
# Clone the test project (gdipak)
git clone https://github.com/2pair/gdipak

# Install project dependencies
cd gdipak
pip install .
```

2. Run PyMOP with the `gdipak` project using all the specifications in the `pymop-artifacts-rv/pymop/specs-new` folder.

You can run PyMOP using one of the following commands:

a. Run with **monkey patching + curse** instrumentation strategy **(recommended)**:
```bash
pytest tests --algo=D --path="$PWD/../pymop-artifacts-rv/pymop/specs-new"
```

b. Run with **monkey patching** instrumentation strategy:
```bash
pytest tests --algo=D --path="$PWD/../pymop-artifacts-rv/pymop/specs-new" --instrument_strategy=builtin
```

c. Run with **monkey patching + AST** instrumentation strategy:
```bash
PYTHONPATH="$PWD/../pymop-artifacts-rv/pymop/pythonmop/pymop-startup-helper" pytest tests --algo=D --path="$PWD/../pymop-artifacts-rv/pymop/specs-new" --instrument_strategy=ast
```

> **Note:** The **monkey patching + curse** strategy (default) is recommended for most cases as it provides the best balance of performance and reliability.

3. Violation Fixing (if applicable)

If the `PyMOP` finds violations, you can find the code place that violates the specification in the testing report printed out in the terminal.

### Re-run the runtime verification tests with the fixed code

After fixing the code, you can re-run the tests using the same command from Step 2 (e.g., `pytest tests --algo=D --path="$PWD/../pymop-artifacts-rv/pymop/specs-new"` for the recommended strategy).

## Installation

There are two ways to install PyMOP: using Docker (recommended) or installing directly on your system.

### Option 1: Docker Installation (Recommended)

The easiest way to get started with PyMOP is using Docker, which ensures all dependencies are properly set up (as described in the tutorial above):

1. Install Docker following the [official instructions](https://docs.docker.com/get-docker/)
2. Build the PyMOP Docker image:
```bash
cd docker_files/demo
docker build -t pymop .
```
3. Run the container:
```bash
docker run -it pymop
```
4. Activate the virtual environment inside the container:
```bash
source pymop-venv/bin/activate
```

### Option 2: Direct Installation

If you prefer to install PyMOP directly on your system, follow these steps:

1. The following dependencies are required to run PyMOP on your local system:
* python3-tk
* python3-venv

2. Create and activate a virtual environment (recommended):
```bash
python -m venv pymop-venv
source pymop-venv/bin/activate  # On Unix/macOS
# or
.\pymop-venv\Scripts\activate  # On Windows
```

3. Clone and install PyMOP:
```bash
git clone https://github.com/allrob23/pymop-artifacts-rv.git
cd pymop-artifacts-rv/pymop
pip install .
```
-->

## Usage

After installation, PyMOP requires setting the `PYTHONPATH` environment variable before running tests. Additional configuration options are available via environment variables (see below).

> **Important:** When using PyMOP, you must set the `PYTHONPATH` environment variable to include the `pymop-startup-helper` directory. This is required for PyMOP to function correctly:
>
> ```bash
> export PYTHONPATH=/path/to/pythonmop/pymop-startup-helper
> pytest tests
> ```
>
> The path should point to the `pymop-startup-helper` directory inside the `pythonmop` folder of your PyMOP installation. This `PYTHONPATH` setting is required for all instrumentation strategies and must be set before running pytest.

## Environment Variables

PyMOP can be configured using environment variables that allow you to customize how it behaves during test runs:

### Core Configuration

**`PYMOP_SPEC_FOLDER`**: Path to the specification folder to be used for the current run.

```bash
export PYMOP_SPEC_FOLDER=/path/to/specs
```

**DEFAULT**: When not provided, the framework will run the tests without performing any runtime verification checks

**`PYMOP_ACTIVE_SPECS`**: The names of the specifications to be checked.

```bash
export PYMOP_ACTIVE_SPECS=Spec1,Spec2
```

**DEFAULT**: When set to `all` or not provided, all specifications in the folder will be used.

**`PYMOP_ALGO`**: The name of the parametric algorithm to be used.

```bash
export PYMOP_ALGO=D
```

Five algorithms are available: `A`, `B`, `C`, `C+`, and `D`. Algorithm `D` is the default algorithm and represents the most complex and comprehensive implementation in PyMOP. You can experiment with other algorithms, though note that there may be performance differences.

**`PYMOP_INSTRUMENTATION_STRATEGY`**: Choose the instrumentation strategy to be used.

```bash
export PYMOP_INSTRUMENTATION_STRATEGY=ast
```

The options are `ast` or `builtin`. Each instrumentation strategy has different benefits and trade-offs. Choose the one that best suits your needs (`ast` is used by default).

**`PYMOP_INSTRUMENT_SITE_PACKAGES`**: Choose whether to instrument site-packages or not.

```bash
export PYMOP_INSTRUMENT_SITE_PACKAGES=true
```

When enabled, PyMOP will instrument code in site-packages directories. This can be slow and take more time for the runtime verification checks to run.

**DEFAULT**: When not set or set to `false`, site-packages will not be instrumented.

> **Note:** Remember to set `PYTHONPATH` to include the `pymop-startup-helper` directory as described in the Usage section above. This is required for PyMOP to function correctly.

### Output and Statistics

**`PYMOP_NO_PRINT`**: Suppresses violation messages from being printed to the terminal at runtime.

```bash
export PYMOP_NO_PRINT=true
```

When set to `false`, violation messages will be printed to the terminal during test execution.

**DEFAULT**: When not set or set to `true`, violation messages will not be printed to the terminal during test execution.

**`PYMOP_STATISTICS`**: Prints statistics about monitors and events.

```bash
export PYMOP_STATISTICS=true
```

When enabled, the plugin will print additional statistics about the runtime verification results, including monitors created and events triggered.

**DEFAULT**: When not set or set to `false`, tests will run normally without printing monitor and event statistics.

**`PYMOP_STATISTICS_FILE`**: Specifies the file path where monitor and event statistics will be stored.

```bash
export PYMOP_STATISTICS_FILE=/path/to/stats.json
```

The file can be either a JSON file or a text file. If not provided, the statistics will be printed to the terminal.

### Debug and Information

**`PYMOP_DEBUG_MSG`**: Prints debug messages for testing purposes.

```bash
export PYMOP_DEBUG_MSG=true
```

When enabled, PyMOP will print debug messages that can help with troubleshooting and development.

**DEFAULT**: When not set or set to `false`, debug messages will not be printed.

**`PYMOP_SPEC_INFO`**: Prints the descriptions of specifications in the spec folder.

```bash
export PYMOP_SPEC_INFO=true
```

When enabled, PyMOP will print detailed descriptions of all specifications found in the spec folder (without running the tests).

**DEFAULT**: When not set or set to `false`, specification descriptions will not be printed.

### Advanced Configuration

**`PYMOP_CONVERT_SPECS`**: Converts front-end specifications to PyMOP internal specifications for correct usage.

```bash
export PYMOP_CONVERT_SPECS=true
```

**DEFAULT**: When not set or set to `false`, specification conversion will not be performed.

**`PYMOP_NO_GARBAGE_COLLECTION`**: Disables garbage collection for the index tree used by PyMOP to store monitors and track events.

```bash
export PYMOP_NO_GARBAGE_COLLECTION=true
```

When enabled, PyMOP will skip garbage collection for the index tree used internally. This may lead to worse performance and increased memory usage.

**DEFAULT**: When not set or set to `false`, garbage collection is enabled.

### Example: Using Multiple Environment Variables

```bash
# Required: Set PYTHONPATH to include pymop-startup-helper
export PYTHONPATH=/path/to/pythonmop/pymop-startup-helper

# Configure PyMOP options
export PYMOP_SPEC_FOLDER=/path/to/specs
export PYMOP_ACTIVE_SPECS=Spec1,Spec2
export PYMOP_ALGO=D
export PYMOP_INSTRUMENTATION_STRATEGY=ast
export PYMOP_INSTRUMENT_SITE_PACKAGES=true
export PYMOP_STATISTICS=true
export PYMOP_STATISTICS_FILE=/path/to/stats.json

# Run tests
pytest tests
```