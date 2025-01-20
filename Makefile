# Available commands
help:
	@echo "make help            - Display this help message"
	@echo "make clean           - Clean up build and dist artifacts"
	@echo "make obfuscate       - Obfuscate Python files using Pyarmor"
	@echo "make build           - Build the built package"
	@echo "make install         - Install the built package"
	@echo "make all             - Run the full workflow: clean, obfuscate, build, and install"

# Clean up build and dist artifacts
clean:
	@echo "Cleaning up build and dist artifacts..."
	pip uninstall sap-hana-to-snowflake-migration -y
	rm -rf dist

# Obfuscate Python files using Pyarmor
obfuscate:
	@echo "Obfuscating Python files using Pyarmor..."
	pyarmor gen -O dist -i app    

# Build the wheel package
build: clean obfuscate 
	@echo "Building the wheel package..."
	python -m build
	
# Install the built wheel package
install: clean obfuscate build
	@echo "Installing the built wheel package..."
	pip install dist/sap_hana_to_snowflake_migration-0.1.0-py3-none-any.whl 

# Full workflow: clean, obfuscate, build, and install
all: clean obfuscate build install
	@echo "Full workflow complete: clean, obfuscate, build, and install"
