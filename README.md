# Cisco Packet Tracer - Discord Rich Presence

[![Build & Release](https://github.com/chawannua/packet-tracer-discord-presence/actions/workflows/build-release.yml/badge.svg)](https://github.com/chawannua/packet-tracer-discord-presence/actions/workflows/build-release.yml)
![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?logo=python)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Security](https://img.shields.io/badge/security-audited%20%26%20verifiable-brightgreen?logo=shield)
![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux-lightgrey)

A lightweight, secure, and modern Discord Rich Presence integration for **Cisco Packet Tracer**. Automatically displays your active topology filename, edit duration, and saved/unsaved status on your Discord profile in real time.

---

## Table of Contents

- [Problem Statement & Security Provenance](#problem-statement--security-provenance)
- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
  - [Option 1: 1-Click Quick Install (Windows)](#-option-1-1-click-quick-install-windows---easiest)
  - [Option 2: Manual Python Setup (Windows / Linux)](#option-2-manual-python-setup-windows--linux)
  - [Option 3: Verified Standalone Executable](#option-3-verified-standalone-executable-windows)
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

### ⚡ Option 1: 1-Click Quick Install (Windows - Easiest)

If you are on Windows, you can install and start the silent background presence service in seconds:

1. Clone or download the repository:
   ```cmd
   git clone https://github.com/chawannua/packet-tracer-discord-presence.git
   cd packet-tracer-discord-presence
   ```
2. Simply double-click **`install.bat`** (or run `.\install.ps1` in PowerShell).

**That's it!** The installer will:
- Automatically create a dedicated `.venv` and install all required libraries.
- Configure a silent Windows Startup entry so it starts automatically in the background on login.
- Launch the background presence process immediately without any console popup.

---

### Option 2: Manual Python Setup (Windows / Linux)

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

### Option 3: Verified Standalone Executable (Windows)

If you prefer a standalone `.exe` without configuring Python:

1. Navigate to the latest release on the [Releases Page](https://github.com/chawannua/packet-tracer-discord-presence/releases).
2. Download `PacketTracerPresence.exe` and `checksums.txt`.
3. Verify the binary checksum with PowerShell:
   ```powershell
   Get-FileHash -Path PacketTracerPresence.exe -Algorithm SHA256
   Get-Content checksums.txt
   ```
   Compare the output hash with `checksums.txt` to guarantee binary authenticity.
4. Double-click `PacketTracerPresence.exe`.

#### Option B: Build the Standalone Executable Yourself
You can build your own standalone binary using PyInstaller:
```powershell
pip install pyinstaller -r requirements.txt
pyinstaller --noconfirm --onefile --name "PacketTracerPresence" --clean main.py
```
The compiled binary will be located in the `dist/` directory:
```powershell
.\dist\PacketTracerPresence.exe --verbose
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

### 3. Antivirus warns about PyInstaller executable
- Windows Defender sometimes flags newly built PyInstaller single-file executables due to heuristic packaging signatures.
- **Remedy**: Build the executable locally with `pyinstaller` on your machine, run via Python directly (Method 1), or verify the SHA-256 hash against our GitHub Actions release provenance.

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
