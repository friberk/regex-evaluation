#!/usr/bin/env python3

import json
import sys
import csv
from typing import Dict


frequency: Dict[str, int] = {}


for file in sys.argv[1:]:
    with open(file, 'r') as report_file:
        report_obj = json.load(report_file)

    for project_name in report_obj:
        project_status = report_obj[project_name]
        result_type = project_status['type']
        inner_result_type = project_status['inner'] if 'inner' in project_status else None

        result_str = f'{result_type} - {inner_result_type["type"]}' if inner_result_type is not None else result_type
        if result_str in frequency:
            frequency[result_str] += 1
        else:
            frequency[result_str] = 1

with open('combined-report.txt', 'w') as output_file:
    writer = csv.writer(output_file)
    writer.writerow(['Package Processing Status', 'Count'])
    sorted_frequencies = {k: v for k, v in sorted(frequency.items(), key=lambda item: item[1], reverse=True)}
    for key in sorted_frequencies:
        writer.writerow([key, frequency[key]])
