#!/bin/sh
pip install -r ./engage_scraper/requirements.txt
pip install -e .
python examples/santamonica_example.py