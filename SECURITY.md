# Security Policy

## Reporting
To report a security vulnerability or sensitive finding, please open an issue or contact the repository maintainer directly.

## Threat Model & Principles
- **Air-Gapped & Local-First:** All calculation modules run entirely offline on local hardware or rig-floor computers. No telemetry, well data, or formation parameters are ever transmitted over external networks.
- **Client-Side In-Browser Execution:** The web application compiles pure Python into WebAssembly via Pyodide. All math executes locally within the client browser sandbox; no server-side backend or external APIs process wellbore data.
- **Zero External Runtime Dependencies:** The core calculation engine ([`src/killsheet/`](src/killsheet/)) depends solely on standard Python libraries (`math`, `typing`, `functools`), eliminating supply-chain exposure from third-party dependencies.
- **No Secrets or Credentials:** This software requires zero credentials, database connections, or API keys. Automated `gitleaks` scans run on every pull request and push to enforce repository hygiene.
