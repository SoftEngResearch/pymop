# PyMOP: A Runtime Verification Tool for Python

## Projects and Data

- **847 Projects**: Find the complete project metadata [here](data/results_metadata.csv)
- **Project Data**: Access all project data files in the [`data`](data) directory
- **Appendix**: See the [appendix](appendix.pdf) for additional details

## Quick links

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Environment Variables](#environment-variables)
- [Output Structure](#output-structure)
- [Run PyMOP on an open-source project](#run-pymop-on-an-open-source-project)
- [Contributing](#contributing)

## System Requirements

PyMOP requires the following components to be installed on your system:

- **Python**: Version 3.12 or later
- **Java**: Version 20 or later
- **Docker**: (optional, but recommended for simplified setup)

## Installation

### Setting up PyMOP with Docker

This is the recommended way to set up PyMOP as it is the easiest way to get started and avoid any dependency issues.

If you don't have Docker installed, follow the instructions [here](https://docs.docker.com/get-docker/) to install Docker.

There are two ways to set up PyMOP using Docker:

1. **Using Docker image provided by PyMOP.** From any directory, run:

   a. Pull the docker image from Docker Hub:
   ```
   docker pull softengresearch/pymop
   ```
   <details>
     <summary>Example Output</summary>
      
      ```
      Using default tag: latest
      latest: Pulling from softengresearch/pymop
      11bf8735fa82: Pull complete 
      5d1190f163bb: Pull complete 
      e2cdfcbb1de3: Pull complete 
      aba73472b256: Pull complete 
      73373b07d07f: Pull complete 
      4f4fb700ef54: Pull complete 
      Digest: sha256:e5745c888a753fcae35c0c063bd17f4616b6c1e0ab431744b0bbae6c69808c7b
      Status: Downloaded newer image for softengresearch/pymop:latest
      docker.io/softengresearch/pymop:latest
      ```
   </details>

   b. Run the Docker container:
   ```
   docker run -it softengresearch/pymop
   ```

   <details>
     <summary>Example Output</summary>
      
      ```
      To run a command as administrator (user "root"), use "sudo <command>".
      See "man sudo_root" for details.

      pymop@c9cbf90079bc:~$
      ```
   </details>

   > **Note:**: The provided image has PyMOP placed in the root directory at `~/pymop`.

   c. Create and activate a virtual environment:
      
      ```bash
      python3 -m venv venv && source venv/bin/activate
      ```

   <details>
     <summary>Example Output</summary>
      
      ```
      To run a command as administrator (user "root"), use "sudo <command>".
      See "man sudo_root" for details.

      ((venv) ) pymop@c9cbf90079bc:~$
      ```
   </details>

   d. Install PyMOP and its dependencies:
      
      ```bash
      pip install -r ~/pymop/requirements.txt && pip install ~/pymop
      ```

   <details>
     <summary>Example Output</summary>
      
      ```
      Collecting pytest (from -r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
      Collecting JPype1 (from -r /home/pymop/pymop/requirements.txt (line 2))
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.0 kB)
      Collecting nltk (from -r /home/pymop/pymop/requirements.txt (line 3))
      Using cached nltk-3.9.2-py3-none-any.whl.metadata (3.2 kB)
      Collecting numpy (from -r /home/pymop/pymop/requirements.txt (line 4))
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
      Collecting iniconfig>=1.0.1 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
      Collecting packaging>=22 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
      Collecting pluggy<2,>=1.5 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
      Collecting pygments>=2.7.2 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
      Collecting click (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
      Collecting joblib (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
      Collecting regex>=2021.8.3 (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
      Collecting tqdm (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached tqdm-4.67.1-py3-none-any.whl.metadata (57 kB)
      Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (495 kB)
      Using cached nltk-3.9.2-py3-none-any.whl (1.5 MB)
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.4 MB)
      Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
      Using cached packaging-26.0-py3-none-any.whl (74 kB)
      Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
      Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (803 kB)
      Using cached click-8.3.1-py3-none-any.whl (108 kB)
      Using cached joblib-1.5.3-py3-none-any.whl (309 kB)
      Using cached tqdm-4.67.1-py3-none-any.whl (78 kB)
      Installing collected packages: tqdm, regex, pygments, pluggy, packaging, numpy, joblib, iniconfig, click, pytest, nltk, JPype1
      Successfully installed JPype1-1.6.0 click-8.3.1 iniconfig-2.3.0 joblib-1.5.3 nltk-3.9.2 numpy-2.4.1 packaging-26.0 pluggy-1.6.0 pygments-2.19.2 pytest-9.0.2 regex-2026.1.15 tqdm-4.67.1

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      Processing ./pymop
      Installing build dependencies ... done
      Getting requirements to build wheel ... done
      Preparing metadata (pyproject.toml) ... done
      Requirement already satisfied: pytest in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (9.0.2)
      Requirement already satisfied: JPype1 in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: nltk in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (3.9.2)
      Requirement already satisfied: numpy in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (2.4.1)
      Requirement already satisfied: packaging in ./venv/lib/python3.12/site-packages (from JPype1->pytest-pythonmop==1.1.0) (26.0)
      Requirement already satisfied: click in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (8.3.1)
      Requirement already satisfied: joblib in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (1.5.3)
      Requirement already satisfied: regex>=2021.8.3 in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (2026.1.15)
      Requirement already satisfied: tqdm in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (4.67.1)
      Requirement already satisfied: iniconfig>=1.0.1 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.3.0)
      Requirement already satisfied: pluggy<2,>=1.5 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: pygments>=2.7.2 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.19.2)
      Building wheels for collected packages: pytest-pythonmop
      Building wheel for pytest-pythonmop (pyproject.toml) ... done
      Created wheel for pytest-pythonmop: filename=pytest_pythonmop-1.1.0-py3-none-any.whl size=2008653 sha256=7d3f6cda9ad1e32d592b53a1785d2b552b9529768fe228b61619efb327bd9b86
      Stored in directory: /tmp/pip-ephem-wheel-cache-mx1w457w/wheels/82/38/25/b5742f168f4f5f646b52c80d87cd371def7bf2e45ba429a108
      Successfully built pytest-pythonmop
      Installing collected packages: pytest-pythonmop
      Successfully installed pytest-pythonmop-1.1.0

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      ```
   </details>

2. **Building your own image from scratch.** This option will take longer than the first option (~10 minutes on our machine) because it will install all the system requirements for PyMOP.

   From the same directory as this `README.md` file, run:

   a. Build the Docker image:
      
      ```bash
      docker build -f Docker/Dockerfile . -t pymop
      ```
   
   <details>
     <summary>Example Output</summary>
      
      ```
      [+] Building 197.1s (10/10) FINISHED                                                                                                           docker:default
      => [internal] load build definition from Dockerfile                                                                                                     0.1s
      => => transferring dockerfile: 1.84kB                                                                                                                   0.0s
      => [internal] load metadata for docker.io/library/ubuntu:22.04                                                                                          0.5s
      => [internal] load .dockerignore                                                                                                                        0.1s
      => => transferring context: 2B                                                                                                                          0.0s
      => [1/6] FROM docker.io/library/ubuntu:22.04@sha256:c7eb020043d8fc2ae0793fb35a37bff1cf33f156d4d4b12ccc7f3ef8706c38b1                                    1.1s
      => => resolve docker.io/library/ubuntu:22.04@sha256:c7eb020043d8fc2ae0793fb35a37bff1cf33f156d4d4b12ccc7f3ef8706c38b1                                    0.0s
      => => sha256:6f4ebca3e823b18dac366f72e537b1772bc3522a5c7ae299d6491fb17378410e 29.54MB / 29.54MB                                                         1.0s
      => [2/6] RUN apt-get update &&     apt-get install -y --no-install-recommends     software-properties-common curl git wget zip rpm vim coreutils bc   110.0s 
      => [3/6] RUN arch=$(uname -m) &&     case "$arch" in         x86_64) JAVA_TARBALL="openjdk-20.0.2_linux-x64_bin.tar.gz" ;;         aarch64) JAVA_TARB  33.7s 
      => [4/6] RUN useradd -ms /bin/bash -c "pymop" pymop && echo "pymop:docker" | chpasswd && adduser pymop sudo                                             0.4s 
      => [5/6] WORKDIR /home/pymop/                                                                                                                           0.1s 
      => [6/6] RUN git clone https://github.com/SoftEngResearch/pymop                                                                                         0.6s 
      => exporting to image                                                                                                                                  51.2s 
      => => exporting layers                                                                                                                                 42.5s 
      => => exporting manifest sha256:6bd4c759b2a446fa04ff8a07854568bcc8caf77544906ac6b7dc45fa0ca4ecf7                                                        0.0s
      => => exporting config sha256:2d37803394c0c4ffcc609cefbdbb4a9d884f539d4193ebf1f8678968b2fe4701                                                          0.0s
      => => exporting attestation manifest sha256:044d40fa54852ca47bcc1024436548faa739256c16f3cd2fda4263022d85b314                                            0.0s
      => => exporting manifest list sha256:d90980c50e2cf40d86c16271624d0eb8a88c00bcdf8d933605e814bfe8758663                                                   0.0s
      => => naming to docker.io/library/pymop:latest                                                                                                          0.0s
      => => unpacking to docker.io/library/pymop:latest                                                                                                       8.6s
      ```
   </details>

   b. Run the Docker container:
      
      ```bash
      docker run -it pymop /bin/bash
      ```

   <details>
      <summary>Example Output</summary>
      
      ```
      To run a command as administrator (user "root"), use "sudo <command>".
      See "man sudo_root" for details.

      pymop@c8d6ebc22ca8:~$
      ```
   </details>

   > **Note:**: The provided image has PyMOP placed in the root directory at `~/pymop`.

   c. Create and activate a virtual environment:
      
      ```bash
      python3 -m venv venv && source venv/bin/activate
      ```

   <details>
     <summary>Example Output</summary>
      
      ```
      To run a command as administrator (user "root"), use "sudo <command>".
      See "man sudo_root" for details.

      ((venv) ) pymop@c9cbf90079bc:~$
      ```
   </details>

   d. Install PyMOP and its dependencies:
      
      ```bash
      pip install -r ~/pymop/requirements.txt && pip install ~/pymop
      ```

   <details>
     <summary>Example Output</summary>
      
      ```
      Collecting pytest (from -r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
      Collecting JPype1 (from -r /home/pymop/pymop/requirements.txt (line 2))
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.0 kB)
      Collecting nltk (from -r /home/pymop/pymop/requirements.txt (line 3))
      Using cached nltk-3.9.2-py3-none-any.whl.metadata (3.2 kB)
      Collecting numpy (from -r /home/pymop/pymop/requirements.txt (line 4))
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
      Collecting iniconfig>=1.0.1 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
      Collecting packaging>=22 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
      Collecting pluggy<2,>=1.5 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
      Collecting pygments>=2.7.2 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
      Collecting click (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
      Collecting joblib (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
      Collecting regex>=2021.8.3 (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
      Collecting tqdm (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached tqdm-4.67.1-py3-none-any.whl.metadata (57 kB)
      Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (495 kB)
      Using cached nltk-3.9.2-py3-none-any.whl (1.5 MB)
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.4 MB)
      Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
      Using cached packaging-26.0-py3-none-any.whl (74 kB)
      Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
      Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (803 kB)
      Using cached click-8.3.1-py3-none-any.whl (108 kB)
      Using cached joblib-1.5.3-py3-none-any.whl (309 kB)
      Using cached tqdm-4.67.1-py3-none-any.whl (78 kB)
      Installing collected packages: tqdm, regex, pygments, pluggy, packaging, numpy, joblib, iniconfig, click, pytest, nltk, JPype1
      Successfully installed JPype1-1.6.0 click-8.3.1 iniconfig-2.3.0 joblib-1.5.3 nltk-3.9.2 numpy-2.4.1 packaging-26.0 pluggy-1.6.0 pygments-2.19.2 pytest-9.0.2 regex-2026.1.15 tqdm-4.67.1

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      Processing ./pymop
      Installing build dependencies ... done
      Getting requirements to build wheel ... done
      Preparing metadata (pyproject.toml) ... done
      Requirement already satisfied: pytest in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (9.0.2)
      Requirement already satisfied: JPype1 in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: nltk in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (3.9.2)
      Requirement already satisfied: numpy in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (2.4.1)
      Requirement already satisfied: packaging in ./venv/lib/python3.12/site-packages (from JPype1->pytest-pythonmop==1.1.0) (26.0)
      Requirement already satisfied: click in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (8.3.1)
      Requirement already satisfied: joblib in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (1.5.3)
      Requirement already satisfied: regex>=2021.8.3 in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (2026.1.15)
      Requirement already satisfied: tqdm in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (4.67.1)
      Requirement already satisfied: iniconfig>=1.0.1 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.3.0)
      Requirement already satisfied: pluggy<2,>=1.5 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: pygments>=2.7.2 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.19.2)
      Building wheels for collected packages: pytest-pythonmop
      Building wheel for pytest-pythonmop (pyproject.toml) ... done
      Created wheel for pytest-pythonmop: filename=pytest_pythonmop-1.1.0-py3-none-any.whl size=2008653 sha256=7d3f6cda9ad1e32d592b53a1785d2b552b9529768fe228b61619efb327bd9b86
      Stored in directory: /tmp/pip-ephem-wheel-cache-mx1w457w/wheels/82/38/25/b5742f168f4f5f646b52c80d87cd371def7bf2e45ba429a108
      Successfully built pytest-pythonmop
      Installing collected packages: pytest-pythonmop
      Successfully installed pytest-pythonmop-1.1.0

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      ```
   </details>

### Setting up without Docker

To run PyMOP without Docker, make sure your system satisfies the requirements listed in the [System Requirements](#system-requirements) section.

1. Clone the PyMOP repository (if you haven't already):
   
   ```bash
   git clone https://github.com/SoftEngResearch/pymop
   cd pymop
   ```

2. Create and activate a virtual environment:
   
   ```bash
   python3 -m venv venv && source venv/bin/activate
   ```

3. Install PyMOP and its dependencies:
   
   ```bash
   pip install -r requirements.txt && pip install .
   ```

   <details>
     <summary>Example Output</summary>
      
      ```
      Collecting pytest (from -r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pytest-9.0.2-py3-none-any.whl.metadata (7.6 kB)
      Collecting JPype1 (from -r /home/pymop/pymop/requirements.txt (line 2))
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (5.0 kB)
      Collecting nltk (from -r /home/pymop/pymop/requirements.txt (line 3))
      Using cached nltk-3.9.2-py3-none-any.whl.metadata (3.2 kB)
      Collecting numpy (from -r /home/pymop/pymop/requirements.txt (line 4))
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
      Collecting iniconfig>=1.0.1 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
      Collecting packaging>=22 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached packaging-26.0-py3-none-any.whl.metadata (3.3 kB)
      Collecting pluggy<2,>=1.5 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
      Collecting pygments>=2.7.2 (from pytest->-r /home/pymop/pymop/requirements.txt (line 1))
      Using cached pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
      Collecting click (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached click-8.3.1-py3-none-any.whl.metadata (2.6 kB)
      Collecting joblib (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached joblib-1.5.3-py3-none-any.whl.metadata (5.5 kB)
      Collecting regex>=2021.8.3 (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
      Collecting tqdm (from nltk->-r /home/pymop/pymop/requirements.txt (line 3))
      Using cached tqdm-4.67.1-py3-none-any.whl.metadata (57 kB)
      Using cached pytest-9.0.2-py3-none-any.whl (374 kB)
      Using cached jpype1-1.6.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (495 kB)
      Using cached nltk-3.9.2-py3-none-any.whl (1.5 MB)
      Using cached numpy-2.4.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.4 MB)
      Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
      Using cached packaging-26.0-py3-none-any.whl (74 kB)
      Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
      Using cached pygments-2.19.2-py3-none-any.whl (1.2 MB)
      Using cached regex-2026.1.15-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (803 kB)
      Using cached click-8.3.1-py3-none-any.whl (108 kB)
      Using cached joblib-1.5.3-py3-none-any.whl (309 kB)
      Using cached tqdm-4.67.1-py3-none-any.whl (78 kB)
      Installing collected packages: tqdm, regex, pygments, pluggy, packaging, numpy, joblib, iniconfig, click, pytest, nltk, JPype1
      Successfully installed JPype1-1.6.0 click-8.3.1 iniconfig-2.3.0 joblib-1.5.3 nltk-3.9.2 numpy-2.4.1 packaging-26.0 pluggy-1.6.0 pygments-2.19.2 pytest-9.0.2 regex-2026.1.15 tqdm-4.67.1

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      Processing ./pymop
      Installing build dependencies ... done
      Getting requirements to build wheel ... done
      Preparing metadata (pyproject.toml) ... done
      Requirement already satisfied: pytest in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (9.0.2)
      Requirement already satisfied: JPype1 in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: nltk in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (3.9.2)
      Requirement already satisfied: numpy in ./venv/lib/python3.12/site-packages (from pytest-pythonmop==1.1.0) (2.4.1)
      Requirement already satisfied: packaging in ./venv/lib/python3.12/site-packages (from JPype1->pytest-pythonmop==1.1.0) (26.0)
      Requirement already satisfied: click in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (8.3.1)
      Requirement already satisfied: joblib in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (1.5.3)
      Requirement already satisfied: regex>=2021.8.3 in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (2026.1.15)
      Requirement already satisfied: tqdm in ./venv/lib/python3.12/site-packages (from nltk->pytest-pythonmop==1.1.0) (4.67.1)
      Requirement already satisfied: iniconfig>=1.0.1 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.3.0)
      Requirement already satisfied: pluggy<2,>=1.5 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (1.6.0)
      Requirement already satisfied: pygments>=2.7.2 in ./venv/lib/python3.12/site-packages (from pytest->pytest-pythonmop==1.1.0) (2.19.2)
      Building wheels for collected packages: pytest-pythonmop
      Building wheel for pytest-pythonmop (pyproject.toml) ... done
      Created wheel for pytest-pythonmop: filename=pytest_pythonmop-1.1.0-py3-none-any.whl size=2008653 sha256=7d3f6cda9ad1e32d592b53a1785d2b552b9529768fe228b61619efb327bd9b86
      Stored in directory: /tmp/pip-ephem-wheel-cache-mx1w457w/wheels/82/38/25/b5742f168f4f5f646b52c80d87cd371def7bf2e45ba429a108
      Successfully built pytest-pythonmop
      Installing collected packages: pytest-pythonmop
      Successfully installed pytest-pythonmop-1.1.0

      [notice] A new release of pip is available: 25.0.1 -> 25.3
      [notice] To update, run: pip install --upgrade pip
      ```
   </details>

## Usage

After installation, PyMOP requires setting the `PYTHONPATH` environment variable before running tests. Additional configuration options are available via environment variables (see [Environment Variables](#environment-variables) section below).

> **Important:** When using PyMOP, you must set the `PYTHONPATH` environment variable to include the `pymop-startup-helper` directory. This is required for PyMOP to function correctly:
>
> ```bash
> export PYTHONPATH=/path/to/pymop/pythonmop/pymop-startup-helper
> pytest tests
> ```
>
> The path should point to the `pymop-startup-helper` directory inside the `pymop/pythonmop` folder of your PyMOP installation. This `PYTHONPATH` setting is required for all instrumentation strategies and must be set before running pytest.

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

> **Note:** Remember to set `PYTHONPATH` to include the `pymop-startup-helper` directory as described in the [Usage](#usage) section above. This is required for PyMOP to function correctly.

### Output and Statistics

**`PYMOP_PRINT_VIOLATIONS_TO_CONSOLE`**: Prints violation messages to the terminal at runtime.

```bash
export PYMOP_PRINT_VIOLATIONS_TO_CONSOLE=true
```

When set to `true`, violation messages will be printed to the terminal during test execution.

**DEFAULT**: When not set or set to `false`, violation messages will not be printed to the terminal during test execution.

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
export PYTHONPATH=/path/to/pymop/pythonmop/pymop-startup-helper

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

## Output Structure

When PyMOP is run with statistics output enabled (e.g. `PYMOP_STATISTICS=yes` and `PYMOP_STATISTICS_FILE` set), three JSON files are written to the current working directory. The filename prefix is the parametric algorithm you used (A, B, C, C+, or D). The table below uses **D** as an example.

| File                | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `D-violations.json` | Unique violations found during execution, with counts for each |
| `D-time.json`       | Timing information measured by PyMOP                           |
| `D-full.json`       | Statistics of PyMOP monitors and events during test execution  |

## Run PyMOP on an open-source project

This section will guide you through how to run PyMOP on an open-source project. You should run the below example inside the Docker container, or in an environment with proper system requirements installed. We will use the [`omergertel/pyformance (sha b71056e)`](https://github.com/omergertel/pyformance.git) project as an example.

> **Demo video:** A step-by-step walkthrough of running PyMOP on the `omergertel/pyformance` example is available [here](https://youtu.be/xIJn0WfiOKc)

1. Set Up Test Project

   ```bash
   # Clone the test project (omergertel/pyformance)
   cd ~ && git clone https://github.com/omergertel/pyformance.git project

   # Create a virtual environment and activate it
   cd project
   python3 -m venv venv
   source venv/bin/activate

   # Install project dependencies
   pip install .
   pip install mock setuptools pytest

   # Run original test (Optional)
   pytest tests
   ```

2. Install PyMOP

   ```bash
   pip install ~/pymop
   ```

3. Run PyMOP with the `omergertel/pyformance` project using all the specifications in the `~/pymop/specs-new` folder.

   You can run PyMOP using one of the following commands:

   a. Run with **monkey patching + AST** instrumentation strategy and parametric algorithm D without monitoring libraries (recommended)
   ```bash
   PYMOP_SPEC_FOLDER=~/pymop/specs-new PYMOP_ALGO=D PYMOP_INSTRUMENTATION_STRATEGY=ast PYMOP_STATISTICS=yes PYMOP_STATISTICS_FILE=D.json PYTHONPATH=~/pymop/pythonmop/pymop-startup-helper/ pytest tests
   ```

   b. Run with **monkey patching + AST** instrumentation strategy and parametric algorithm C without monitoring libraries
   ```bash
   PYMOP_SPEC_FOLDER=~/pymop/specs-new PYMOP_ALGO=C PYMOP_INSTRUMENTATION_STRATEGY=ast PYMOP_STATISTICS=yes PYMOP_STATISTICS_FILE=C.json PYTHONPATH=~/pymop/pythonmop/pymop-startup-helper/ pytest tests
   ```

   c. Run with **monkey patching + AST** instrumentation strategy and parametric algorithm D without monitoring libraries while printing the violations (if any) during test execution to the terminal
   ```bash
   PYMOP_SPEC_FOLDER=~/pymop/specs-new PYMOP_ALGO=D PYMOP_INSTRUMENTATION_STRATEGY=ast PYMOP_PRINT_VIOLATIONS_TO_CONSOLE=yes PYMOP_STATISTICS=yes PYMOP_STATISTICS_FILE=D.json PYTHONPATH=~/pymop/pythonmop/pymop-startup-helper/ pytest -s tests
   ```

   d. Run with **monkey patching + AST** instrumentation strategy and parametric algorithm D without monitoring libraries while printing the violations at the end of the test execution to the terminal
   ```bash
   PYMOP_SPEC_FOLDER=~/pymop/specs-new PYMOP_ALGO=D PYMOP_INSTRUMENTATION_STRATEGY=ast PYMOP_PRINT_VIOLATIONS_TO_CONSOLE=yes PYTHONPATH=~/pymop/pythonmop/pymop-startup-helper/ pytest -s tests
   ```

   e. Run with **monkey patching + AST** instrumentation strategy and parametric algorithm D with libraries monitored
   ```bash
   PYMOP_SPEC_FOLDER=~/pymop/specs-new PYMOP_ALGO=D PYMOP_INSTRUMENTATION_STRATEGY=ast PYMOP_INSTRUMENT_SITE_PACKAGES=yes PYMOP_STATISTICS=yes PYMOP_STATISTICS_FILE=D.json PYTHONPATH=~/pymop/pythonmop/pymop-startup-helper/ pytest tests
   ```

More options can be found in the [Environment Variables](#environment-variables) section.

## Contributing

We are accepting issues and pull requests. We welcome all who are interested to help fix issues.