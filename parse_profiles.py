#!/usr/bin/env python
"""
usage:
    parse_profiles.py [options] --dir=<profiles-dir>
    parse_profiles.py [options] <profile-html>...

options:
    --traceback  Print an exception stack trace on errors
"""

import re
import sys
import json
import pathlib
import traceback

import docopt
from bs4 import BeautifulSoup


def parse_profile(path):
    try:
        with open(path, 'rb') as f:
            html = BeautifulSoup(f.read(), 'html.parser')

        id = get_zwift_id(html)
        zp_points = get_zp_points(html)
        aliases = get_aliases(html)

    except Exception as e:
        raise ValueError(f'Unable to parse {path}: {e}') from e

    return {'zwiftid': id, 'zwiftpower_points': zp_points, 'aliases': aliases}


def get_zwift_id(html):
    # It appears in a few places, but this is easy enough. There's a bunch of
    # data defined in javascript in the head.
    js_data = '\n'.join(script.string for script in html.select('head script'))
    match = re.search(r'\bzwift_id *: *[\'"](\d+)[\'"]', js_data)

    if not match:
        raise ValueError(f'Unable to find Zwift ID in HTML')

    return int(match.group(1))


def get_zp_points(html):
    html.find(id='profile_information').select('tr')

    for tr in html.select('#profile_information tr'):
        th = tr.find('th')
        td = tr.find('td')
        if th and td and any(s.strip().lower() == 'racing licence' for s in th.findAll(text=True)):
            match = re.match(r'^(\d+(?:\.\d+)?)', ''.join(s for s in td.findAll(text=True) if s.strip()))
            if match:
                return float(match.group(1))
    return None


def get_aliases(profile_html):
    alias_rows = profile_html.select('#profile_rider_names tbody > tr')
    return [parse_alias_row(row) for row in alias_rows]


def require_match(regex, string):
    match = re.match(regex, string)
    if match is None:
        raise ValueError(f'failed to match regex {regex!r} against {string!r}')
    return match


def parse_alias_row(row):
    date, time, name, weight, height = [''.join(td.findAll(text=True)).strip() for td in row.find_all('td')]

    date_match = require_match(r'^([A-Za-z]{3}) ([\d]{1,2})[a-z]{2}$', date)
    time_match = require_match(r'^([\d]{2}):([\d]{2})$', time)
    weight_match = require_match(r'^([\d(\.\d+)?]+)kg$', weight)
    height_match = require_match(r'^([\d]+)cm$', height)

    return {
        'month': date_match.group(1).lower(),
        'day': int(date_match.group(2)),
        'hour': int(time_match.group(1)),
        'minute': int(time_match.group(2)),
        'name': name,
        'weight': float(weight_match.group(1)),
        'height': int(height_match.group(1)),
    }


def parse_profiles(paths, print_traceback=False):
    for path in paths:
        try:
            yield parse_profile(path)
        except ValueError as e:
            print(f'Error: unable to parse profile data from {path}: {e}',
                  file=sys.stderr)
            if print_traceback:
                print(file=sys.stderr)
                traceback.print_exc()


def main():
    args = docopt.docopt(__doc__)

    if args['--dir']:
        profiles = pathlib.Path(args['--dir']).glob('profile_*.html')
    else:
        profiles = args['<profile-html>']

    # produce stream of whitespace-separate JSON objects, suitable for jq
    for profile_data in parse_profiles(profiles,
                                       print_traceback=args['--traceback']):
        print(json.dumps(profile_data, indent=None))


if __name__ == '__main__':
    main()
