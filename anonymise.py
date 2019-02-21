#!/usr/bin/env python
"""
Anonymise a stream of suspicious change descriptions from
find_profile_changes.py

Usage:
    anonymise.py

One JSON obj per line on stdin, one anonymised JSON obj out on stdout.

Anonymisation steps:
    - Zwift ID is removed
    - ZwiftPower points are rounded to nearest 50
    - dates are rounded to 12 hour (am/pm) periods
"""
import json
import sys
import docopt


def main():
    docopt.docopt(__doc__)

    for line in sys.stdin:
        desc = json.loads(line)

        anon_desc = {
            'zwiftid': None,
            'zwiftpower_points': round(desc['zwiftpower_points'] / 50) * 50,
            'suspicious_profile_changes': [
                {'date': pc['date'][:7] + ('am' if int(pc['date'][7:9]) < 12
                                           else 'pm'),
                 'height_change': pc['height_change']}
                for pc in desc['suspicious_profile_changes']
            ]
        }
        print(json.dumps(anon_desc))


if __name__ == '__main__':
    main()
