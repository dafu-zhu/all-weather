# Scripts Directory

**Purpose**: Machine-read experimental scripts directory.

This directory contains one-off scripts, experiments, and runner files. It is NOT meant for careful human organization - feel free to create new scripts here without worrying about structure.

## Current Scripts

### Runner Scripts (moved from root)
- `run_v2_strategy.py` - Run v2.0 strategy on 7-ETF dataset
- `run_v2_7etf.py` - Compare 7-ETF vs 8-ETF vs 5-ETF
- `run_v2_enhanced.py` - Run v2.0 on 8-ETF (with 30yr bond)
- `run_clean_comparison.py` - Compare old vs clean data quality

### Data Scripts
- `fetch_data_akshare.py` - Fetch ETF data from akshare

## Usage

Run any script from the project root:
```bash
cd /path/to/all-weather
python scripts/run_v2_strategy.py
```

## Guidelines

- ✓ Create new experimental scripts freely
- ✓ No need to maintain or organize
- ✓ Scripts may have dependencies on root structure
- ✓ Use for quick tests, data exploration, one-off analyses
- ✗ Don't put production code here (use `src/` instead)
- ✗ Don't put documentation notebooks here (use `notebooks/` instead)
