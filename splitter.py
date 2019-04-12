#    Copyright [2019] [Abraham Monrroy Cano]
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import sys
import rosbag
import subprocess
import yaml
import os
from pathlib import Path
import argparse


def show_progress(percent, length= 80):
    sys.stdout.write('\x1B[2K')  # Erase entire current line
    sys.stdout.write('\x1B[0E')  # Move to the beginning of the current line
    progress = "Progress: ["
    for i in range(0, length):
        if i < length * percent:
            progress += '='
        else:
            progress += ' '
    progress += "] " + str(round(percent * 100.0, 2)) + "%"
    sys.stdout.write(progress)
    sys.stdout.flush()


def main(args):
    parser = argparse.ArgumentParser(description='Rosbag splitter.')
    parser.add_argument('in_file', nargs=1, help='input bag file')
    parser.add_argument('out_path', nargs='+', help='output path to store the split files')
    parser.add_argument('split_period', nargs='+', help='Time in seconds to split')

    args = parser.parse_args()

    bagfile = args.in_file[0]
    out_path = args.out_path[0]
    split_period = int(args.split_period[0])

    split_count = 0

    info_dict = yaml.load(
        subprocess.Popen(['rosbag', 'info', '--yaml', bagfile], stdout=subprocess.PIPE).communicate()[0])
    bag_duration = info_dict['duration']
    start_time = info_dict['start']

    if split_period > bag_duration:
        print(
            'Input Bag file cannot be split. The specified period ({period})is longer than the bag duration ({duration}).'.format(
                period=split_period, duration=bag_duration))
        exit(1)

    base_name = Path(bagfile).stem

    filename = "{}.{}.bag".format(os.path.join(out_path, base_name), split_count)
    split_count = split_count + 1

    outbag = rosbag.Bag(filename, 'w')
    split_start_time = start_time

    for topic, msg, t in rosbag.Bag(bagfile).read_messages():
        if (t.to_sec() - split_start_time) > split_period:
            outbag.close()
            filename = "{}.{}.bag".format(os.path.join(out_path, base_name), split_count)
            split_count = split_count + 1
            split_start_time = t.to_sec()
            outbag = rosbag.Bag(filename, 'w')

        outbag.write(topic, msg, t)
        percent = (t.to_sec() - start_time) / bag_duration
        show_progress(percent)

    outbag.close()


if __name__ == "__main__":
    main(sys.argv[1:])
