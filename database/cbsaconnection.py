##BARA TEST
##Script to run the view.py file in cbsa_tools


import json
import sys
sys.path.append('../')  # Add the parent directory of cbsa_tools to the Python path

from cbsa_tools.view import main

def run_view_script(dataset, part, input_file, start_time, duration, output_format):
    # Call the main function of view.py with the provided arguments
    data = main([
        '--dataset', dataset,
        '--part', part,
        '--input', input_file,
        '--start', start_time,
        '--duration', duration,
        '--start', start_time,  # Repeated argument
        '--duration', duration,  # Repeated argument
        '--format', output_format
    ])

    # Process the JSON data
    for line in data.split('\n'):
        if line.strip():  # Check if the line is not empty
            json_data = json.loads(line)
            # Do something with the JSON data
            print(json_data)  # For example, print each JSON object

if __name__ == '__main__':
    # Example usage
    run_view_script(
        dataset='WORLDCUP98',
        part='wc_day90_1',
        input_file='worldcup98.zip',
        start_time='1998-07-24T00:48:00',
        duration='1h',
        output_format='json'
    )