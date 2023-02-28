# Sailor Hat for Raspberry Pi: Daemon

[![Build status](https://github.com/hatlabs/shrpid/workflows/build/badge.svg?branch=master&event=push)](https://github.com/hatlabs/shrpid/actions?query=workflow%3Abuild)
[![Python Version](https://img.shields.io/pypi/pyversions/shrpid.svg)](https://pypi.org/project/shrpid/)
[![Dependencies Status](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen.svg)](https://github.com/hatlabs/shrpid/pulls?utf8=%E2%9C%93&q=is%3Apr%20author%3Aapp%2Fdependabot)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-green.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/hatlabs/shrpid/blob/master/.pre-commit-config.yaml)
[![Semantic Versions](https://img.shields.io/badge/%20%20%F0%9F%93%A6%F0%9F%9A%80-semantic--versions-e10079.svg)](https://github.com/hatlabs/shrpid/releases)
[![License](https://img.shields.io/github/license/hatlabs/shrpid)](https://github.com/hatlabs/shrpid/blob/master/LICENSE)
![Coverage Report](assets/images/coverage.svg)


> **Note**
>
> There are two different versions of SH-RPi. Version 1 was released in 2021 and includes an integrated CAN controller for connecting to the NMEA 2000 bus. It uses different daemon software than version 2. Version 1 software is archived to the <a href="https://github.com/hatlabs/SH-RPi-daemon/tree/v1"><b>v1</b> branch</a> of this repository.
>
> The description below applies to the current version 2 of SH-RPi. Version 2 is available for purchase at <a href="https://hatlabs.fi/"><b>hatlabs.fi</b></a>.


## Introduction

[SH-RPi](https://shop.hatlabs.fi/products/sh-rpi), formally known as Sailor Hat for Raspberry Pi,
is a Raspberry Pi smart power management board. The main features are:

- Power management with a 60 Farad supercapacitor that provides so-called last gasp energy for shutting down the device in a controlled fashion after the system power is cut.
- Peak power management: The same supercapacitor circuitry is able to provide peak current for power-hungry devices such as the Raspberry Pi 4B with SSD or NVMe drives, allowing those devices to be powered using current-limited subcircuits such as the NMEA2000 bus power wires.
- Protection circuitry: The board is protected against noisy 12V/24V voltages commonly present on vehicles or marine vessels.
- A battery-powered real-time clock circuit, allowing for the device to keep time even in the absence of GPS or networking.
  
`shrpid` is a power monitor and watchdog for the SH-RPi. It communicates with the SH-RPi device, providing the "smart" aspects of the operation. Supported features include:

- Blackout reporting if input voltage falls below a defined threshold
- Triggering of device shutdown if power isn't restored
- Supercap voltage reporting
- Watchdog functionality: if the SH-RPi receives no communication for 10 seconds, the SH-RPi will hard reset the device.
- RTC sleep mode: the onboard real-time clock can be set to boot the Raspberry Pi at a specific time. This is useful for battery powered devices that should perform scheduled tasks such as boat battery and bilge level monitoring.

The main use case for the service software is to have the Raspberry Pi shut down once the power is cut. This prevents potential file system corruption without having to shut down the device manually.

## Installation

Copy and paste the following lines to your terminal to install the latest version of the daemon and to update the configuration files:

    curl -L \
        https://raw.githubusercontent.com/hatlabs/SH-RPi-daemon/main/install.sh \
        | sudo bash

## SH-RPi documentation

For a more detailed SH-RPi documentation, please visit the [documentation website](https://docs.hatlabs.fi/sh-rpi).

## Getting the hardware

Sh-RPi devices are available for purchase at [shop.hatlabs.fi](https://shop.hatlabs.fi/).

----

## 🛠️ Development Instructions

### Building and releasing your package

Building a new version of the application contains steps:

- Bump the version of your package `poetry version <version>`. You can pass the new version explicitly, or a rule such as `major`, `minor`, or `patch`. For more details, refer to the [Semantic Versions](https://semver.org/) standard.
- Make a commit to `GitHub`.
- Create a `GitHub release`.
- And... publish 🙂 `poetry publish --build`

### Development features

- Supports for `Python 3.9` and higher.
- [`Poetry`](https://python-poetry.org/) as the dependencies manager. See configuration in [`pyproject.toml`](https://github.com/hatlabs/shrpid/blob/master/pyproject.toml) and [`setup.cfg`](https://github.com/hatlabs/shrpid/blob/master/setup.cfg).
- Automatic codestyle with [`black`](https://github.com/psf/black), [`isort`](https://github.com/timothycrosley/isort) and [`pyupgrade`](https://github.com/asottile/pyupgrade).
- Ready-to-use [`pre-commit`](https://pre-commit.com/) hooks with code-formatting.
- Type checks with [`mypy`](https://mypy.readthedocs.io); docstring checks with [`darglint`](https://github.com/terrencepreilly/darglint); security checks with [`safety`](https://github.com/pyupio/safety) and [`bandit`](https://github.com/PyCQA/bandit)
- Testing with [`pytest`](https://docs.pytest.org/en/latest/).
- Ready-to-use [`.editorconfig`](https://github.com/hatlabs/shrpid/blob/master/.editorconfig), [`.dockerignore`](https://github.com/hatlabs/shrpid/blob/master/.dockerignore), and [`.gitignore`](https://github.com/hatlabs/shrpid/blob/master/.gitignore). You don't have to worry about those things.

### Deployment features

- `GitHub` integration: issue and pr templates.
- `Github Actions` with predefined [build workflow](https://github.com/hatlabs/shrpid/blob/master/.github/workflows/build.yml) as the default CI/CD.
- Everything is already set up for security checks, codestyle checks, code formatting, testing, linting, docker builds, etc with [`Makefile`](https://github.com/hatlabs/shrpid/blob/master/Makefile#L89). More details in [makefile-usage](#makefile-usage).
- [Dockerfile](https://github.com/hatlabs/shrpid/blob/master/docker/Dockerfile) for your package.
- Always up-to-date dependencies with [`@dependabot`](https://dependabot.com/). You will only [enable it](https://docs.github.com/en/github/administering-a-repository/enabling-and-disabling-version-updates#enabling-github-dependabot-version-updates).
- Automatic drafts of new releases with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). You may see the list of labels in [`release-drafter.yml`](https://github.com/hatlabs/shrpid/blob/master/.github/release-drafter.yml). Works perfectly with [Semantic Versions](https://semver.org/) specification.

### Open source community features

- Ready-to-use [Pull Requests templates](https://github.com/hatlabs/shrpid/blob/master/.github/PULL_REQUEST_TEMPLATE.md) and several [Issue templates](https://github.com/hatlabs/shrpid/tree/master/.github/ISSUE_TEMPLATE).
- Files such as: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` are generated automatically.
- [`Stale bot`](https://github.com/apps/stale) that closes abandoned issues after a period of inactivity. (You will only [need to setup free plan](https://github.com/marketplace/stale)). Configuration is [here](https://github.com/hatlabs/shrpid/blob/master/.github/.stale.yml).
- [Semantic Versions](https://semver.org/) specification with [`Release Drafter`](https://github.com/marketplace/actions/release-drafter).

## Installation

```bash
pip install -U shrpid
```

or install with `Poetry`

```bash
poetry add shrpid
```

## Using with Conda

Conda users can setup a development environtment with ideas [stolen from Stack Overflow](https://stackoverflow.com/a/71110028/2999754).

```bash
conda create --name shrpid --file conda-linux-64.lock
conda activate shrpid
poetry install
```

and during regular use:

```bash
conda activate shrpid
```

Conda environment can be updated as follows:

```bash
# Re-generate Conda lock file(s) based on environment.yml
conda-lock -k explicit --conda mamba
# Update Conda packages based on re-generated lock file
mamba update --file conda-linux-64.lock
# Update Poetry packages and re-generate poetry.lock
poetry update
```

### Makefile usage

[`Makefile`](https://github.com/hatlabs/shrpid/blob/master/Makefile) contains a lot of functions for faster development.

<details>
<summary>1. Download and remove Poetry</summary>
<p>

To download and install Poetry run:

```bash
make poetry-download
```

To uninstall

```bash
make poetry-remove
```

</p>
</details>

<details>
<summary>2. Install all dependencies and pre-commit hooks</summary>
<p>

Install requirements:

```bash
make install
```

Pre-commit hooks coulb be installed after `git init` via

```bash
make pre-commit-install
```

</p>
</details>

<details>
<summary>3. Codestyle</summary>
<p>

Automatic formatting uses `pyupgrade`, `isort` and `black`.

```bash
make codestyle

# or use synonym
make formatting
```

Codestyle checks only, without rewriting files:

```bash
make check-codestyle
```

> Note: `check-codestyle` uses `isort`, `black` and `darglint` library

Update all dev libraries to the latest version using one comand

```bash
make update-dev-deps
```

</p>
</details>

<details>
<summary>4. Code security</summary>
<p>

```bash
make check-safety
```

This command launches `Poetry` integrity checks as well as identifies security issues with `Safety` and `Bandit`.

```bash
make check-safety
```

</p>
</details>

<details>
<summary>5. Type checks</summary>
<p>

Run `mypy` static type checker

```bash
make mypy
```

</p>
</details>

<details>
<summary>6. Tests with coverage badges</summary>
<p>

Run `pytest`

```bash
make test
```

</p>
</details>

<details>
<summary>7. All linters</summary>
<p>

Of course there is a command to ~~rule~~ run all linters in one:

```bash
make lint
```

the same as:

```bash
make test && make check-codestyle && make mypy && make check-safety
```

</p>
</details>

<details>
<summary>8. Docker</summary>
<p>

```bash
make docker-build
```

which is equivalent to:

```bash
make docker-build VERSION=latest
```

Remove docker image with

```bash
make docker-remove
```

More information [about docker](https://github.com/hatlabs/shrpid/tree/master/docker).

</p>
</details>

<details>
<summary>9. Cleanup</summary>
<p>
Delete pycache files

```bash
make pycache-remove
```

Remove package build

```bash
make build-remove
```

Delete .DS_STORE files

```bash
make dsstore-remove
```

Remove .mypycache

```bash
make mypycache-remove
```

Or to remove all above run:

```bash
make cleanup
```

</p>
</details>

## 📈 Releases

You can see the list of available releases on the [GitHub Releases](https://github.com/hatlabs/shrpid/releases) page.

We follow [Semantic Versions](https://semver.org/) specification.

We use [`Release Drafter`](https://github.com/marketplace/actions/release-drafter). As pull requests are merged, a draft release is kept up-to-date listing the changes, ready to publish when you’re ready. With the categories option, you can categorize pull requests in release notes using labels.

### List of labels and corresponding titles

|               **Label**               |  **Title in Releases**  |
| :-----------------------------------: | :---------------------: |
|       `enhancement`, `feature`        |       🚀 Features       |
| `bug`, `refactoring`, `bugfix`, `fix` | 🔧 Fixes & Refactoring  |
|       `build`, `ci`, `testing`        | 📦 Build System & CI/CD |
|              `breaking`               |   💥 Breaking Changes   |
|            `documentation`            |    📝 Documentation     |
|            `dependencies`             | ⬆️ Dependencies updates |

You can update it in [`release-drafter.yml`](https://github.com/hatlabs/shrpid/blob/master/.github/release-drafter.yml).

GitHub creates the `bug`, `enhancement`, and `documentation` labels for you. Dependabot creates the `dependencies` label. Create the remaining labels on the Issues tab of your GitHub repository, when you need them.
