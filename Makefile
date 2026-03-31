.PHONY: dev test clean lint slither gas-report

# Start the local development environment (Anvil + contract deployer)
dev:
	docker compose up --build

# Run all tests using the CI profile
test:
	FOUNDRY_PROFILE=ci forge test -vvv

# Run Slither analysis and print findings
slither:
	slither . --config-file .slither.conf
	python3 tools/parse-slither.py slither-output.json

# Generate gas snapshot for current state
gas-report:
	forge snapshot --snap .gas-snapshot

# Run linting and formatting checks
lint:
	forge fmt --check

# Clean all build artifacts
clean:
	forge clean
	docker compose down -v
	rm -f slither-output.json .gas-snapshot-*
