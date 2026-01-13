# Outback Stockbook

A fast, offline-first livestock and paddock manager for Australian cattle and sheep producers. Built with PySide6 (Qt for Python) and SQLite for complete offline capability.

## Features

### Core Functionality (MVP)

- **Herd Register**: Track individual animals by EID/visual tag, mob, breed, sex, DOB, and status
- **Mob Management**: Group animals into mobs for bulk operations
- **Paddock Tracking**: Manage paddocks with area, notes, and current mob assignments
- **Movement Records**: Timeline of animal and mob movements between paddocks
- **Treatment Tracking**: Record treatments with automatic withholding period (WHP) calculation
- **Weight Recording**: Individual weights with condition scores and ADG calculations
- **PDF Reports**: Treatment register, movement log, WHP clearance, sale draft, inventory
- **Backup/Restore**: Simple database backup and restore functionality

### Key Differentiators

- **Offline-first**: Works without internet - essential for rural Australia
- **Fast data entry**: Big buttons, keyboard shortcuts, bulk actions
- **Australian compliance**: PIC fields, NLIS-style records, treatment register format
- **No subscription**: One-time purchase, your data stays on your computer

## Installation

### Requirements

- Python 3.10 or higher
- Windows, macOS, or Linux

### Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/Outback-Stockbook.git
cd Outback-Stockbook

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m stockbook.main
```

### Install as package

```bash
pip install -e .
stockbook  # Run the application
```

## Usage

### First Run

1. Launch the application
2. Go to **Settings** to enter your property information (name, PIC)
3. Add your **Paddocks** first
4. Create **Mobs** and assign them to paddocks
5. Add **Animals** to your mobs
6. Set up **Products** (treatments/vaccines) with their withholding periods

### Daily Operations

**Recording a treatment:**
1. Go to **Animals** view
2. Select one or more animals
3. Click **Record Treatment**
4. Select product, enter dose and batch number
5. WHP end dates are calculated automatically

**Moving animals:**
1. Go to **Animals** or **Mobs** view
2. Select animals/mob to move
3. Click **Move to Mob** or **Move Mob to Paddock**

**Recording weights:**
1. Go to **Animals** view
2. Select animals to weigh
3. Click **Record Weight**
4. Enter weight and optional condition score

### Keyboard Shortcuts

- `Ctrl+F`: Focus search bar
- `Alt+1` to `Alt+8`: Navigate between views
- `Escape`: Clear search

## Data Model

All data is stored in a local SQLite database at `~/.outback-stockbook/stockbook.db`.

### Core Tables

- `animals`: Individual animals with EID, visual tag, breed, sex, DOB, status
- `mobs`: Animal groups for management
- `paddocks`: Property areas with area and notes
- `events`: Base table for all event types (movement, treatment, weigh, etc.)
- `products`: Treatment products with withholding periods
- `tasks`: Generated reminders and to-do items

### Event Types

Everything is recorded as an "event" which makes reporting and audit trails simple:
- Movement
- Treatment
- Weigh
- Death
- Sale
- Birth
- Pregnancy Test
- Joining
- Note

## Reports

Available PDF reports:

1. **Treatment Register**: All treatments within a date range
2. **Movement Log**: Animal/mob movements between paddocks
3. **WHP Clearance List**: Animals currently under withholding period
4. **Sale Draft Sheet**: Animals ready for sale (excludes those on WHP)
5. **Animal Inventory**: Complete animal list by status
6. **Weight Summary**: Weight records with statistics

## Backup & Restore

Regular backups are recommended:

1. Go to **Settings** > **Backup & Restore**
2. Click **Create Backup**
3. Save the `.db` file to a safe location (USB drive, cloud storage)

To restore:
1. Go to **Settings** > **Backup & Restore**
2. Click **Restore from Backup**
3. Select your backup file
4. Confirm the restore operation

## Project Structure

```
Outback-Stockbook/
├── src/
│   └── stockbook/
│       ├── __init__.py
│       ├── main.py              # Application entry point
│       ├── models/
│       │   ├── database.py      # SQLite database management
│       │   └── entities.py      # Data classes for domain objects
│       ├── services/
│       │   └── pdf_reports.py   # PDF report generation
│       ├── ui/
│       │   ├── main_window.py   # Main window with sidebar
│       │   ├── views/           # Main content views
│       │   │   ├── dashboard.py
│       │   │   ├── animals.py
│       │   │   ├── mobs.py
│       │   │   ├── paddocks.py
│       │   │   ├── treatments.py
│       │   │   ├── weights.py
│       │   │   ├── reports.py
│       │   │   └── settings.py
│       │   ├── dialogs/         # Modal dialogs
│       │   └── widgets/         # Reusable widgets
│       └── utils/
├── tests/
├── resources/
│   ├── icons/
│   └── styles/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

### Running tests

```bash
pip install -e ".[dev]"
pytest
```

### Code style

```bash
black src/
ruff check src/
```

## Roadmap

### Post-MVP Features

- Bluetooth scale head import (CSV/serial)
- NLIS upload helper
- Multi-user LAN mode
- Drought feeding module
- Property biosecurity checklist

## License

Proprietary - All rights reserved.

## Support

For support and feature requests, please contact the development team.
