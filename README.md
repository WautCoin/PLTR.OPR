# PLTR.OPR — Operation Reporting Tool

A lightweight CLI tool for creating, tracking, and summarizing operational reports.

## Requirements

- Python 3.8+

## Usage

```bash
# Create a new report
python opr.py create "Database connection failure" -d "Primary DB unreachable" -s critical

# List all reports
python opr.py list

# Filter by status
python opr.py list --status open

# Show report details
python opr.py show 1

# Update a report
python opr.py update 1 --status in_progress
python opr.py update 1 -t "New title" --severity high

# Delete a report
python opr.py delete 1

# Summary statistics
python opr.py summary
```

## Severity levels

`low` | `medium` (default) | `high` | `critical`

## Status values

`open` (default) → `in_progress` → `resolved` → `closed`

## Storage

Reports are persisted to `opr_data.json` in the working directory.
Override with the `OPR_STORAGE` environment variable:

```bash
OPR_STORAGE=/var/data/opr.json python opr.py list
```

## Tests

```bash
pip install pytest
python -m pytest test_opr.py -v
```