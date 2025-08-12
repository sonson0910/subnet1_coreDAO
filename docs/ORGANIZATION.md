# Subnet1 Aptos - Project Organization

## Directory Structure

```
subnet1_aptos/
├── subnet1/              # Subnet implementation
├── scripts/              # Utility scripts
├── tests/                # Test files
├── docs/                 # Documentation
├── config/               # Configuration files
├── registration/         # Registration scripts
├── setup/                # Setup and creation scripts
├── fixes/                # Fix and debug scripts
├── transfers/            # Transfer and mint scripts
├── entities/             # Entity configurations
├── backup/               # Backup of original files
└── .git/                 # Git repository
```

## File Organization

### Tests (`tests/`)
- All test files (`test_*.py`, `*_test.py`, `debug_*.py`)
- Test configuration files

### Scripts (`scripts/`)
- Utility scripts (`quick_*.py`, `check_*.py`, etc.)
- Maintenance and deployment scripts

### Documentation (`docs/`)
- Markdown files
- Text documentation

### Configuration (`config/`)
- JSON, YAML, TOML configuration files
- Settings and parameters

### Registration (`registration/`)
- Registration scripts (`register_*.py`, `start_*.py`, `run_*.py`)
- Network startup scripts

### Setup (`setup/`)
- Setup scripts (`setup_*.py`, `create_*.py`, `update_*.py`)
- Environment creation scripts

### Fixes (`fixes/`)
- Fix scripts (`fix_*.py`, `comprehensive_fix*.py`)
- Debug and troubleshooting scripts

### Transfers (`transfers/`)
- Transfer scripts (`transfer_*.py`, `send_*.py`, `mint_*.py`)
- Token and asset management scripts

## Import Paths

All import paths have been updated to reflect the new organization.
If you encounter import errors, please check the updated paths.

## Migration Notes

- Critical files like `__init__.py`, `setup.py`, etc. remain in their original locations
- Test files are now in the `tests/` directory
- Registration scripts are organized in the `registration/` directory
- Setup scripts are in the `setup/` directory
- Fix scripts are in the `fixes/` directory
- Transfer scripts are in the `transfers/` directory

## Development

When adding new files:
1. Place test files in `tests/`
2. Place utility scripts in `scripts/`
3. Place documentation in `docs/`
4. Place configuration files in `config/`
5. Place registration scripts in `registration/`
6. Place setup scripts in `setup/`
7. Place fix scripts in `fixes/`
8. Place transfer scripts in `transfers/`

This organization makes the project more maintainable and easier to navigate.
