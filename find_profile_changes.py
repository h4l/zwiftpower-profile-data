#!/usr/bin/env python
"""
Scan a stream of JSON profiles created by parse_profiles.py for height
changes.

Usage:
    find_profile_changes.py [options]

Options:
    --format=<fmt>
        The output format to produce: csv, json or json-stream

    --sort
        Sort the output by ZwiftPower points (descending)
"""

import csv
import itertools
import json
import sys

import docopt


def stream_profiles(fileobj):
    for line in (l.strip() for l in fileobj):
        if not line:
            continue

        try:
            yield json.loads(line)
        except Exception as e:
            raise ValueError(
                f'Unable to parse input line as JSON: {line}') from e


def describe_suspicious_profile(profile):
    suspicious_deltas = get_suspicious_deltas(
        backfill_heights(profile['aliases']))

    if not suspicious_deltas:
        return None

    return {
        'zwiftid': profile['zwiftid'],
        'zwiftpower_points': profile['zwiftpower_points'],
        'suspicious_profile_changes': [
            describe_suspicious_delta(d) for d in suspicious_deltas
        ]
    }


def describe_suspicious_delta(delta):
    return {
        'date': format_date(delta['to']),
        'height_change': delta['deltas']['height']
    }


def get_suspicious_deltas(aliases):
    return filter_deltas(get_deltas(aliases, fields=['height']),
                         retain={'height': lambda x: abs(x) >= 5})


def format_date(o):
    return f"{o['month'].capitalize()} {o['day']} {o['hour']:02}:{o['minute']:02}"


def filter_deltas(deltas, *, retain):
    """
    Example:
        >>> filter_deltas([{'deltas': {'foo': 2, 'bar': 1}}, {'deltas': {'foo': 5}}],
        ...               retain={'foo': lambda x: abs(x) > 3})
        [{'deltas': {'bar': 1}}, {'deltas': {'foo': 5}}]
        >>> filter_deltas([{'deltas': {'foo': 2}}, {'deltas': {'foo': 5}}],
        ...               retain={'bar': lambda x: False})
        [{'deltas': {'foo': 2}}, {'deltas': {'foo': 5}}]
    """
    filtered = (
        {**d,
         'deltas': {k: v for k, v in d['deltas'].items()
                    if retain.get(k, lambda x: True)(v)}}
        for d in deltas
    )

    return [d for d in filtered if d['deltas']]


def get_deltas(aliases, fields):
    """

    Example:
        >>> aliases = [
        ...   {"month": "jan", "day": 15, "hour": 0, "minute": 28, "weight": 82.0, "height": 187},
        ...   {"month": "jan", "day": 10, "hour": 2, "minute": 28, "weight": 82.0, "height": 120},
        ...   {"month": "jan", "day": 10, "hour": 0, "minute": 28, "weight": 82.0, "height": 120},
        ...   {"month": "jan", "day": 1, "hour": 0, "minute": 28, "weight": 82.0, "height": 187},
        ... ]
        >>> list(get_deltas(aliases, ['height', 'weight']))
        [{'from': {...}, 'to': {...}, 'deltas': {'height': 67}}, {'from': {...}, 'to': {...}, 'deltas': {'height': -67}}]
        >>> list(get_deltas(aliases, ['weight']))
        []
    """

    last = None
    for alias in aliases:
        if last is not None:
            deltas = {f: last[f] - alias[f] for f in fields
                      if last[f] - alias[f] != 0}

            if deltas:
                yield {
                    'from': alias,
                    'to': last,
                    'deltas': deltas
                }
        last = alias


def backfill_heights(aliases):
    """
    ZP only started recording heights on ~18th Feb, dates before that have
    0s for height. Backfill these with the last value.

    Example:
        >>> backfill_heights([{'height': 10}, {'height': 9}, {'height': 0},
        ...                     {'height': 10}, {'height': 0}, {'height': 0}])
        [{'height': 10}, {'height': 9}, {'height': 0}, {'height': 10}, {'height': 10}, {'height': 10}]
        >>> backfill_heights([])
        []
    """
    try:
        first_height = next(
            a['height'] for a in aliases[::-1] if a['height'] != 0)
    except StopIteration:
        # People with no aliases, and people who've not changed their profile
        # since height was recorded. We'll just keep the 0s and no deltas will
        # be found.
        return aliases

    backfilled = [
        {**a, 'height': first_height} for a in
        itertools.takewhile(lambda a: a['height'] == 0, aliases[::-1])][::-1]

    default = list(itertools.dropwhile(lambda a: a['height'] == 0,
                                       aliases[::-1]))[::-1]

    return default + backfilled


def estimate_relative_years(aliases):
    year = 0
    last_month = None
    for alias in aliases:
        if last_month is not None and aliases['month'] > last_month:
            year -= 1

        yield {**aliases, 'relative_year': year}
        last_month = alias['month']


def numeric_months(aliases):
    return [{**alias, 'month': numeric_month(alias['month'])}
            for alias in aliases]


months = {month: n for n, month in
          enumerate(('jan feb mar apr may jun '
                     'jul aug sep oct nov dec').split(), 1)}


def numeric_month(month):
    """
        >>> numeric_month('jan')
        1
        >>> numeric_month('jun')
        6
        >>> numeric_month('dec')
        12
    """
    return months[month]


def output_json_stream(descs, fileobj):
    for desc in descs:
        print(json.dumps(desc, indent=None), file=fileobj)


def output_json(descs, fileobj):
    json.dump(list(descs), fileobj, indent=2)


def output_csv(descs, fileobj):
    writer = csv.DictWriter(fileobj, ['profile_url', 'zwiftpower_points',
                                      'date', 'height_change'])

    writer.writeheader()
    writer.writerows(
        {**change,
         'zwiftpower_points': desc['zwiftpower_points'],
         'profile_url':
             f'https://www.zwiftpower.com/profile.php?z={desc["zwiftid"]}'}
        for desc in descs
        for change in desc['suspicious_profile_changes'])


formats = {
    'json-stream': output_json_stream,
    'json': output_json,
    'csv': output_csv,
}


def main():
    args = docopt.docopt(__doc__)

    format = 'json-stream' if args['--format'] is None else args['--format']
    if format not in formats:
        raise SystemExit(f'Unknown --format value: {format!r}')

    potential_descriptions = (describe_suspicious_profile(profile)
                              for profile in stream_profiles(sys.stdin))
    descs = (d for d in potential_descriptions if d is not None)

    if args['--sort']:
        descs = sorted(descs,
                       key=lambda d: (d['zwiftpower_points'], d['zwiftid']))

    formats[format](descs, sys.stdout)


if __name__ == '__main__':
    main()
