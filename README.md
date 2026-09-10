# Cisco Packet Tracer - Discord Rich Presence

[![Build & Release](https://github.com/chawannua/packet-tracer-discord-presence/actions/workflows/build-release.yml/badge.svg)](https://github.com/chawannua/packet-tracer-discord-presence/actions/workflows/build-release.yml)
![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python)
[![Version](https://img.shields.io/github/v/release/chawannua/packet-tracer-discord-presence?color=blue&label=version&style=flat-square)](https://github.com/chawannua/packet-tracer-discord-presence/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Security](https://img.shields.io/badge/security-audited%20%26%20verifiable-brightgreen?logo=shield)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey)

A lightweight, secure, and modern Discord Rich Presence integration for **Cisco Packet Tracer**. Automatically displays your active topology filename, edit duration, and saved/unsaved status on your Discord profile in real time.

<p align="center">
  <img src="assets/preview.png" alt="Cisco Packet Tracer Discord Rich Presence Preview" width="500">
</p>

---

## Table of Contents

- [Problem Statement & Security Provenance](#problem-statement--security-provenance)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
  - [Recommended: 1-Click Install (Windows)](#-recommended-1-click-install-windows)
  - [Manual Python Setup (Windows / Linux)](#manual-python-setup-windows--linux)
  - [Optional: Standalone Executable](#optional-standalone-executable-windows)
- [Command-Line Flags & Configuration](#command-line-flags--configuration)
- [Troubleshooting](#troubleshooting)
- [Development & Testing](#development--testing)
- [Contributing](#contributing)
- [License](#license)

---

## Problem Statement & Security Provenance

Many legacy Discord Rich Presence scripts for Cisco Packet Tracer distributed pre-compiled, opaque `.exe` binaries directly in source control without public build scripts, audit trails, or reproducible pipelines. These binaries often triggered antivirus false-positives, required elevated administrator permissions, suffered from high CPU polling, and carried substantial security risks.

### Why This Repository is Safe & Trusted:

1. **Zero Untrusted Binaries**:
   - All legacy opaque binaries (`.exe`, `.lnk`) have been purged from the repository history.
   - The repository contains **100% open-source, auditable Python code**.
2. **Transparent CI/CD & Build Provenance**:
   - Standalone Windows executables are compiled transparently using [GitHub Actions](.github/workflows/build-release.yml) on clean, hosted `windows-latest` virtual machines directly from git tags.
   - Every build step and dependency is fully recorded in the workflow logs.
3. **Cryptographic Verification**:
   - Each official release includes an automated `checksums.txt` with SHA-256 hashes generated during the GitHub Actions build run. You can verify that downloaded binaries have not been tampered with.
4. **No Administrator Privileges Required**:
   - Runs strictly within standard user-space permissions. It does not touch protected system registry keys or require administrative escalation.
5. **Privacy Respecting**:
   - The application communicates **exclusively** with your local Discord client via standard IPC pipes (`pypresence`). No telemetry, analytics, or external outbound network calls are made.

---

## Key Features

- **Multi-Version Cisco Packet Tracer Support**:
  - Automatically identifies running instances of Cisco Packet Tracer **7.x**, **8.x**, and **9.x** across Windows (`PacketTracer.exe`, `PacketTracer7.exe`, `PacketTracer8.exe`, `PacketTracer9.exe`) and Linux (`PacketTracer`).
- **Ultra-Lightweight PID Caching**:
  - Employs smart process handle caching. After initial discovery, polling checks only the cached process ID (`psutil.pid_exists`) rather than traversing the entire system process table, keeping CPU usage and battery consumption negligible (<0.1%).
- **Dynamic Topology & Window State Parsing**:
  - Reads active window titles to extract the current project or lab name (`.pkt` / `.pka`).
  - Detects unsaved modifications (denoted by an asterisk `*`) and updates your Discord status accordingly (`Saved` vs `Unsaved changes`).
- **Discord Rate Limit Protection**:
  - Enforces Discord RPC rate-limit compliance (15-second update throttle) with intelligent state deduplication so Discord connections never get dropped or throttled.
- **Resilient Auto-Reconnection**:
  - Gracefully recovers from Discord client restarts or Packet Tracer closures without crashing.
- **Customizable CLI**:
  - Configurable polling intervals, Discord Application Client ID override, and verbose debug diagnostics.

---

## How It Works

```
 ┌───────────────────────────┐         ┌───────────────────────────────┐
 │   Cisco Packet Tracer     │         │       Discord Desktop         │
 │  (PID / Window Title)     │         │          Client               │
 └─────────────┬─────────────┘         └───────────────▲───────────────┘
               │                                       │
               │ Window Title / PID                    │ Local IPC Pipe
               ▼                                       │ (Rate-limited: 15s)
 ┌─────────────────────────────────────────────────────┴───────────────┐
 │                       packet-tracer-discord-presence                        │
 │                                                                     │
 │   [ProcessDetector]       [WindowParser]          [RPCManager]      │
 │    PID Caching             Regex Parser            Throttling       │
 │    Low CPU Polling         Unsaved State Detection State Dedup      │
 └─────────────────────────────────────────────────────────────────────┘
```

When active, your Discord profile displays:
- **Details**: 
  - Lab with live assessment percentage: `Lab: <LabName>.pka (75%)` (or `(Timer: 00:15:30)`)
  - Topology name: `Topology: <ProjectName>.pkt`
  - Unsaved canvas: `Designing New Topology`
- **State**: 
  - Active Device & Applet / IOS Prompt: `<Device> > <Applet> (<Prompt>)` (e.g. `Laptop0 > Terminal (Switch#)` or `Router0 > CLI (Router(config)#)`)
  - Device Configuration: `Configuring: <Device>` (e.g. `Configuring: Router0`)
  - Canvas Workspace Mode: `Mode: <Realtime|Simulation> (<Logical|Physical>)`
- **Large Image**: Cisco Packet Tracer logo (`Cisco Packet Tracer`)
- **Small Image & Tooltip**: Dynamic device hardware icon (`router`, `switch`, `laptop`, `pc`, `server`, `phone`) with current status tooltip
- **Timestamp**: Elapsed session duration

---

## Quick Start

**Install from source — it is the supported path.** It takes two commands, never gets flagged by antivirus, and auto-starts on login. The standalone `.exe` is optional and comes with a caveat (see below).

### ⚡ Recommended: 1-Click Install (Windows)

1. Clone the repository:
   ```cmd
   git clone https://github.com/chawannua/packet-tracer-discord-presence.git
   cd packet-tracer-discord-presence
   ```
2. Double-click **`install.bat`** (or run `.\install.ps1` in PowerShell).

That's it. The installer will:
- Create a dedicated `.venv` and install all required libraries.
- Offer to install Python via `winget` if you don't have it.
- Configure a silent Windows Startup entry so it runs automatically on login.
- Launch the background presence process immediately, with no console popup.

---

### Manual Python Setup (Windows / Linux)

If you prefer to run or customize the source manually:

#### Prerequisites
- Python **3.9** or newer
- Cisco Packet Tracer installed
- Discord Desktop client open and running

#### 1. Clone the repository
```bash
git clone https://github.com/chawannua/packet-tracer-discord-presence.git
cd packet-tracer-discord-presence
```

#### 2. Create and activate a virtual environment
- **On Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```
- **On Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
```

#### 4. Run the presence daemon
```bash
python main.py
```
Or run with verbose debug logs:
```bash
python main.py --verbose
```

---

### Optional: Standalone Executable (Windows)

> **Heads up:** the release build is unsigned, and Windows Defender flags unsigned PyInstaller binaries as a **false positive** — it may quarantine or auto-delete the download. This is a known PyInstaller issue, not a problem with this code. If it happens, either allow the file in Defender (**Windows Security → Virus & threat protection → Protection history → Allow**) or just use the source install above, which avoids the issue entirely.

If you'd rather not install Python:

1. Go to the [Releases Page](https://github.com/chawannua/packet-tracer-discord-presence/releases).
2. Download `PacketTracerPresence-windows.zip` and `checksums.txt`.
3. Verify the checksum in PowerShell:
   ```powershell
   Get-FileHash -Path PacketTracerPresence-windows.zip -Algorithm SHA256
   Get-Content checksums.txt
   ```
4. Extract the zip and run `PacketTracerPresence.exe` from inside the extracted folder.
   Keep the folder intact — the exe needs the files beside it.

#### Build it yourself
```powershell
pip install pyinstaller -r requirements.txt
pyinstaller --noconfirm --onedir --name "PacketTracerPresence" --clean main.py
```
Output lands in `dist\PacketTracerPresence\`:
```powershell
.\dist\PacketTracerPresence\PacketTracerPresence.exe --verbose
```

---

## Command-Line Flags & Configuration

`packet-tracer-discord-presence` can be configured via CLI flags:

| Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--interval` | `float` | `5.0` | Polling frequency (in seconds) to check process and window state. |
| `--client-id` | `string` | `1351548975567736923` | Custom Discord Application Client ID. |
| `--verbose` | `flag` | `False` | Enables detailed debug logging in the console. |
| `--launch` | `flag` | `False` | Launch Discord Presence in background mode. |
| `--version` | `flag` | - | Display current version and exit. |
| `-h`, `--help` | `flag` | - | Display help information and exit. |

### Example CLI Usages:

```bash
# Increase polling interval to 10 seconds with verbose logging
python main.py --interval 10 --verbose

# Use a custom Discord Application Client ID
python main.py --client-id 123456789012345678
```

---

## Troubleshooting

### 1. Discord status does not appear or says "Disconnected"
- **Discord Desktop App**: Ensure you are running the official Discord Desktop application. Discord Web in a browser cannot receive local IPC connections.
- **Activity Privacy Settings**: In Discord, navigate to **User Settings > Activity Privacy** and ensure **"Display current activity as a status message"** is toggled **ON**.
- **Startup Order**: Open Discord *before* or *after* running the script; the script will automatically retry connecting every 15 seconds.

### 2. Cisco Packet Tracer is running but presence shows "Idling" or "Workspace"
- If you have an unsaved or untitled project, Packet Tracer sets the window title to `Cisco Packet Tracer` without a filename. Save your project (`.pkt`) to display the project name.
- If using an unusual Packet Tracer fork or version, verify its process name matches one of `PacketTracer.exe`, `PacketTracer7.exe`, `PacketTracer8.exe`, `PacketTracer9.exe`, or `PacketTracer`.

### 3. Windows Defender flagged or deleted the .exe
This is a **false positive**. Defender flags the stock PyInstaller bootloader generically because malware also uses PyInstaller, and unsigned binaries have no reputation to vouch for them.

- **Best fix**: use the [1-click source install](#-recommended-1-click-install-windows). No binary, no flag.
- **Or allow it**: Windows Security → Virus & threat protection → Protection history → find the item → **Allow**.
- **Or verify then allow**: check the SHA-256 against `checksums.txt` from the release (built in public by [GitHub Actions](.github/workflows/build-release.yml)), then allow it.

Releases ship as a `--onedir` zip rather than a single self-extracting `.exe`, which avoids the runtime-unpacking behavior that triggers most heuristics.

---

## Development & Testing

This project follows clean coding standards and includes a comprehensive automated test suite.

### Installing Development Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests
Execute unit tests across all modules:
```bash
pytest -v
```

### Code Style & Linting
Verify code compliance with PEP 8 and Flake8:
```bash
# Critical errors
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Complexity and style
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

---

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Add unit tests for your changes in `tests/`.
4. Run `pytest` and `flake8` to ensure all tests and lints pass.
5. Commit your changes: `git commit -m "Add amazing feature"`.
6. Push to your branch and open a Pull Request against `main`.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for complete details.
