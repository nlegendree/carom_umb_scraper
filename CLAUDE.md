# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**UMB Carom Scraper** is a complete automation system for UMB (Union Mondiale de Billard) tournament registration. It combines web scraping, intelligent date calculation, and multi-strategy bots for ultra-fast tournament registration.

### Key Features
- Automated UMB tournament scraping with World Cup 3-Cushion detection
- Intelligent registration date calculation
- Multi-player simultaneous registration system
- Two bot strategies: cURL (ultra-fast) and Selenium (robust)
- Unified CLI interface for all operations

## Development Setup

- **Python version**: 3.12+ (specified in `pyproject.toml`)
- **Package manager**: uv (recommended) with fallback to pip
- **Virtual environment**: `.venv` (gitignored)
- **Browser**: Chrome/Chromium required for Selenium bot

## Installation Commands

### With uv (recommended)
```bash
uv sync                    # Install all dependencies
uv add <package-name>      # Add production dependency
uv add --dev <package-name> # Add development dependency
```

### With pip (fallback)
```bash
pip install -r requirements.txt
```

## Project Architecture

### Core Modules
- **`src/scraper/`** - Main scraping and configuration logic
  - `scraper.py` - UMB website scraper with World Cup detection
  - `config_manager.py` - Centralized configuration management
  - `players_manager.py` - Multi-player profile management

- **`src/bots/`** - Registration bot implementations
  - `base_bot.py` - Shared configuration and utilities
  - `curl_bot.py` - Ultra-fast HTTP-based bot
  - `selenium_bot.py` - Browser-based robust bot
  - `multi_launcher.py` - Multi-player orchestration system

### Configuration Structure
- **`config/players/`** - Individual player profiles (JSON)
  - `template.json` - Template for new players (tracked in git)
  - `*.json` - Individual player files (gitignored except template)
- **`config/tournaments/`** - Tournament configurations (gitignored directory, structure tracked)
- **`config/bot_config.json`** - Bot timing and behavior settings (tracked in git)

### Data Flow
1. **Scraping**: `scraper.py` → `data/umb_tournaments.json`
2. **Configuration**: CLI → player profiles + tournament configs
3. **Registration**: Bots → UMB registration forms
4. **Logging**: All operations → `logs/*.log`

## Common Development Tasks

### Running the Application
```bash
# Main CLI interface
python main.py <command>

# Direct bot execution
python -m src.bots.curl_bot --config <config> --player <player>
python -m src.bots.selenium_bot --config <config> --player <player>
python -m src.bots.multi_launcher --config <multi_config>
```

### Key CLI Commands
```bash
# Tournament management
python main.py scrape                    # Scrape tournaments
python main.py world-cups                # Show future World Cups

# Player management  
python main.py list-players              # List all players with validation status
python main.py create-player <name>      # Create new player from template
python main.py validate-player <name>    # Validate player configuration

# Bot setup
python main.py setup-bot <tournament_id> --player <name>                    # Single player
python main.py setup-bot <tournament_id> --players <name1,name2>            # Multi-player
python main.py setup-bot <tournament_id> --players <name1:curl,name2:selenium> # Mixed bots
```

## Code Conventions

### Import Structure
```python
# Standard library
import json
import sys
from pathlib import Path

# Third-party
import requests
from selenium import webdriver

# Local modules (relative imports in packages)
from .config_manager import config_manager
from scraper.config_manager import config_manager  # Cross-package
```

### Configuration Patterns
- All configs are JSON files with clear field validation
- Player configs follow standardized `player_data` structure
- Tournament configs include timing and synchronization settings
- Bot configs centralize timing parameters and behavior flags

### Error Handling
- Comprehensive validation with user-friendly error messages
- Graceful degradation for network issues
- Detailed logging for debugging bot behavior
- Screenshot capture for Selenium bot failures

### Performance Considerations
- cURL bot: 100ms check intervals during critical windows
- Multi-launcher: 50ms delays between bot spawning
- Memory-efficient scraping with selective data retention
- Optimized browser settings for Selenium (disabled images, etc.)

## Testing Strategy

### Manual Testing
- Use `validate-player` for configuration verification
- Test bot setup without actual registration (dry-run capability)
- Monitor logs for timing and performance validation

### Configuration Testing
- Template validation for new player creation
- Multi-player configuration generation testing
- Tournament date calculation verification

## Security Notes

- Player data contains PII (email, personal info) - keep gitignored
- No hardcoded credentials or sensitive data in tracked files
- Log files may contain personal information - keep gitignored
- Browser automation respects rate limiting and server load

## File Management

### Tracked Files (in git)
- Source code (`src/`)
- Configuration templates (`config/players/template.json`, `config/bot_config.json`)
- Documentation (`README.md`, `CLAUDE.md`)
- Project files (`pyproject.toml`, `requirements.txt`)

### Ignored Files (gitignored)
- Player profiles (`config/players/*.json` except template)
- Tournament configurations (`config/tournaments/*.json`)
- Generated data (`data/*.json`, `data/*.csv`)
- Logs (`logs/*`)
- Python artifacts (`__pycache__/`, `.venv/`)

## Development Notes

### Multi-Player System
The multi-player functionality uses process isolation with synchronized launching:
- Each player gets their own bot process
- Configurable delays between launches (default 50ms)
- Real-time monitoring with success/failure tracking
- Support for mixing cURL and Selenium bots in single command

### Bot Strategy Selection
- **cURL**: Use for maximum speed, reliable network conditions
- **Selenium**: Use for complex JavaScript sites, visual debugging
- **Mixed**: Combine both strategies for optimal coverage

### Date Calculation Logic
World Cup registration dates are calculated as:
- Tournament start date minus 14 days
- Registration opens at 12:00:00 local time
- Bot monitoring starts 5 minutes before target time

When modifying date calculation logic, ensure backward compatibility with existing tournament data.