#!/bin/bash
set -eu -o pipefail

# Create a whitespace-separated dataset of ZwiftPower "alias" data on stdout

find profiles -name 'profile_*.html' | parallel --progress -n 100 ./parse_profiles.py '{}'
