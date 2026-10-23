# Security Architecture & Operations

## 1. Core Principles

- **Local-First & Air-Gapped:** The calculations are engineered for critical rig-site environments where internet access is intermittent or prohibited. Zero data leaves the local workstation.
- **Client-Side In-Browser Execution:** The web application (`web/index.html`) compiles pure Python into WebAssembly via Pyodide. No remote backend, API proxy, or cloud database ever receives well geometry or formation pressure data.
- **Zero Supply-Chain Risk for Core Solver:** The core library ([`src/killsheet/`](../src/killsheet/)) contains **zero external dependencies**, relying exclusively on Python 3.10+ standard libraries.
- **No Secrets or PII:** The framework manages mathematical models and wellbore physics; no API keys, credentials, or proprietary coordinates are stored.

---

## 2. Automated Security Verification

- **Gitleaks CI:** Scans all commits, pull requests, and git history for accidentally staged secrets.
- **Pre-commit Hooks:** Enforces file hygiene, TOML/YAML syntax verification, and secret scanning prior to commit.
