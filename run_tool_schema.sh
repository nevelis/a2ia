#!/bin/bash
cd /home/aaron/dev/nevelis/a2ia
python3 scripts/generate_tool_schema.py
echo "Exit code: $?"
ls -lh tools*.* template_example.txt 2>&1 || echo "Files not created"

