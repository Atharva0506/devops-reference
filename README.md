# StabilityNexus DevOps Reference

Reference implementation of the standardized CI/CD pipeline for StabilityNexus and DjedAlliance repositories.

This repo demonstrates the full DevSecOps toolchain running on a real codebase. Open a PR against `main` and watch the pipeline:

1. **Forge tests** run with the CI profile (`via_ir = false`, `fuzz.runs = 256`)
2. **Slither** scans for security vulnerabilities and posts findings as a PR comment
3. **Gas delta** report compares gas usage between base and PR branches
4. **Gitleaks** scans for accidentally committed secrets
5. **CodeRabbit** automatically reviews code quality (free for OSS)

## Quick Start

```bash
git clone https://github.com/StabilityNexus/devops-reference.git
cd devops-reference
make dev
```

This starts Anvil (local EVM on port 8545) and deploys contracts automatically.

## Run Tests

```bash
make test
```

## Run Slither Locally

```bash
make slither
```

## Structure

```
.github/workflows/
  contract-ci.yml       # CI workflow: tests, Slither, gas report, Gitleaks
contracts/
  InvoiceManager.sol    # Demo contract with deliberate reentrancy for Slither
  interfaces/
    IERC20.sol          # Minimal ERC-20 interface
tools/
  parse-slither.py      # Parses Slither JSON into PR comment markdown
  gas-delta.py          # Compares gas snapshots into PR comment markdown
.slither.conf           # Slither config with documented false positive suppressions
.gitleaks.toml          # Secret detection rules for Ethereum keys
.coderabbit.yaml        # CodeRabbit auto-review configuration
docker-compose.yml      # Anvil + contract deployer
foundry.toml            # Foundry config with separate CI profile
Makefile                # dev, test, slither, gas-report, lint, clean
```

## Adopting for Your Repo

1. Copy `.github/workflows/contract-ci.yml`, `.slither.conf`, and `tools/` to your repo
2. Edit `foundry.toml` to add a `[profile.ci]` section
3. Change the `solidity-version` in the workflow if needed
4. Install CodeRabbit GitHub App (free for public repos)
5. Copy `.gitleaks.toml` for secret detection

Three config variables. One PR. Full CI baseline.

 
