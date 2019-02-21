#!/bin/bash
set -eu -o pipefail

# Generate a list of profile URLs for aria2 on stdout
# Output looks like:
#
#   https://zwiftpower.com/profile.php?z=123
#    out=profile_123.html

curl --fail --silent 'https://zwiftpower.com/api3.php?do=rider_list' | \
    jq --raw-output '.data[].zwid | tostring | gsub("[^0-9]"; "-") |  @uri "https://zwiftpower.com/profile.php?z=\(.)", " out=profile_\(.).html"'
