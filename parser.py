import re
import os
import sys
import argparse
import datetime
from collections import Counter, namedtuple

code_counter = Counter()
response_size_counter = Counter()

# datetime format
date_fmt = '%d-%m-%y'
time_fmt = '%H-%M-%S'

# regular expression
r = re.compile(r"\[pid: .*?in (?P<vars>\d+) bytes.* \[(?P<date>.*)\]"
               " (?P<method>.*) /.*? generated (?P<generated>\d+)"
               " .*? \(HTTP/.*? (?P<code>\d+)\) .*? headers in (?P<head>\d+)")


class Duration:
    """Helper class for global var"""

    def __init__(self):
        self.first_time = 0
        self.last_time = 0

    @property
    def duration(self):
        diff = self.last_time - self.first_time

        if diff != 0:
            return diff.seconds
        return diff


def validate_datetime(datetime_value):
    """Validate input from/to datetime format"""
    try:
        date, time = datetime_value.split('_')
    except ValueError as e:
        print('Something wrong with datetime.', e)
        sys.exit(1)

    time = '-'.join(
        time.split('-') + (['00'] * (3 - len(time.split('-')))))

    try:
        dt = datetime.datetime.strptime(
            '_'.join([date, time]), '%d-%m-%Y_%H-%M-%S')
        return dt
    except ValueError as e:
        print('Something wrong with datetime.', e)
        sys.exit(1)


def process_line(line_match, datetime_start, datetime_end):
    """Process each file line with re match"""
    line_group_dict = line_match.groupdict()
    line_datetime = datetime.datetime.strptime(
        line_group_dict['date'], '%a %b %d %H:%M:%S %Y')

    if datetime_start < line_datetime < datetime_end:

        if not duration.first_time:
            duration.first_time = line_datetime
            duration.last_time = line_datetime
        else:
            duration.last_time = line_datetime

        code_counter[line_group_dict['code']] += 1
        response_size_counter[line_group_dict['code']] += float(
            line_group_dict['vars'])


def process_file(datetime_start, datetime_end, file_name):
    """Process file line by line"""
    try:
        f = open(file_name, 'r')
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    else:
        with f:
            for line in f.readlines():
                line_match = r.search(line)
                if line_match:
                    process_line(line_match, datetime_start, datetime_end)

        show_result()


def show_result():
    """show results"""
    if duration.duration != 0:
        rate = sum(code_counter.values())/duration.duration
    else:
        rate = 0

    code_counts = [(int(k), v) for k, v in code_counter.items()]
    code_counts = sorted(code_counts, key=lambda x: x[0])

    print('Zapytan: {}\n'
          'Zapytania/sec: {:.2f}\n'
          'Odpowiedzi: {}\n'
          'Sredni rozmiar zapytan 2xx: {:.2f} bytes'.format(
              sum(code_counter.values()),
              rate,
              code_counts,
              calc_mean_size(code_counter, response_size_counter, '2..')))


def calc_mean_size(code_counter, response_size_counter, code_pattern):
    """Calculate mean size of response for group of codes"""
    val_sum = 0
    count_sum = 0
    code_avg = []
    for code in code_counter:

        if re.match(code_pattern, code):
            count_sum += code_counter[code]
            val_sum += response_size_counter[code]
            code_avg.append(val_sum / count_sum)
    try:
        return sum(code_avg) / len(code_avg)
    except ZeroDivisionError:
        return 0


if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='Simple uWSGI logs parser')
    argparser.add_argument(
        '-f', '--from', dest='start',
        nargs='?', default=None)
    argparser.add_argument(
        '-t', '--to', dest='end', nargs='?', default=None)
    argparser.add_argument(
        'file_name')
    args = argparser.parse_args()

    if args.start:
        datetime_start = validate_datetime(args.start)
    else:
        datetime_start = datetime.datetime.min
    if args.end:
        datetime_end = validate_datetime(args.end)
    else:
        datetime_end = datetime.datetime.max

    duration = Duration()

    process_file(datetime_start, datetime_end, args.file_name)
