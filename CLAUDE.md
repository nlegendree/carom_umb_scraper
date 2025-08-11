# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for scraping carom billiards tournament data from UMB (Union Mondiale de Billard). The project is in early development stage with a basic structure.

## Development Setup

- Python version: 3.9 (specified in `.python-version`)
- Package manager: uv (uses `pyproject.toml`)
- Virtual environment: `.venv` (gitignored)

## Common Commands

### Running the Application
```bash
python main.py
```

### Package Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package-name>

# Add development dependency  
uv add --dev <package-name>
```

## Project Structure

- `main.py` - Entry point with basic hello world functionality
- `pyproject.toml` - Project configuration and dependencies
- `.python-version` - Python version specification for pyenv/uv
- `.gitignore` - Standard Python gitignore patterns

## Architecture Notes

The project is currently minimal with just a basic entry point. As the scraper functionality is developed, consider organizing into modules for:
- Web scraping logic
- Data parsing and validation
- Data storage/output
- Configuration management