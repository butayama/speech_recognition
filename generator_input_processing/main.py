r"""
main.py
simulate a workflow:
generator file name input
processing files in a while True try except loop
output results in files an other directory
"""
import csv
import os
from sys import version_info

pathname = os.path.join("E:\\", "HiDrive", "generative_art", "files_to_process")
target_pathname = os.path.join("E:\\", "GitHub", "generator_input_processing", "processed_files")


def do_something_with_file_content(csv_path):
    print('csv_path = ', csv_path)
    go_header_ = []
    stone_color_ = []
    x_coordinate_ = []
    y_coordinate_ = []
    z_coordinate_ = []

    with open(csv_path) as go_csv:
        go_ob = csv.reader(go_csv, delimiter=str(','))

        # Loop through the csv file, recording the header and the data
        for v in go_ob:
            if not go_header_:
                go_header_ = v
            else:
                v = [str(v[0]),
                     int(v[1]),
                     int(v[2]),
                     int(v[3])]
                stone_color_.append(v[0])
                x_coordinate_.append(v[1])
                y_coordinate_.append(v[2])
                z_coordinate_.append(v[3])
    return stone_color_, x_coordinate_, y_coordinate_, z_coordinate_


def store_new_file_content(py_filename_, base_name_, stone_color_, x_coordinate_, y_coordinate_, z_coordinate_, take):
    csv_path = os.path.join(py_filename_, base_name_ + f"new_content_{take}.csv")
    note_header = ["pitch", "duration", "dynamic", "pan", "length"]
    note_lines = [note_header]

    v = [[], [], [], []]
    for i, item in enumerate(z_coordinate_):
        v[0].append(stone_color_[i])
        v[1].append(x_coordinate_[i])
        v[2].append(y_coordinate_[i])
        v[3].append(item)
    v[1].sort()
    v[2].sort()
    v[3].sort()
    for k in range(len(v[3])):
        note_lines.append([str(v[j][k]) for j in range(len(v))])

    if version_info[0] < 3:
        # with open(csv_path, 'wb') as note_file: # python2 OK
        infile = open(csv_path, 'wb')
    else:
        # with open(csv_path, 'w', newline='') as note_file: # python3 OK
        infile = open(csv_path, 'w+', newline='')
    with infile as note_file:
        note_writer = csv.writer(note_file)
        note_writer.writerows(note_lines)


def main_loop():
    base_name = "not_defined_yet"
    py_filename = "not_defined_yet"
    processed_files = 0
    parse_csv = (f for f in os.listdir(pathname) if f.endswith(".csv"))
    while True:
        try:
            names = parse_csv
            filename = next(names)
            base_name, _ = os.path.splitext(os.path.basename(filename))
            py_filename = target_pathname
            stone_color, x_coordinate, y_coordinate, z_coordinate = \
                do_something_with_file_content(os.path.join(pathname, filename))
            processed_files += 1
            store_new_file_content(py_filename, base_name, stone_color, x_coordinate,
                                   y_coordinate, z_coordinate, processed_files)
        except TypeError as e:
            print(e)
            print(f"{py_filename + base_name + '.csv'} could not be processed")
        except StopIteration:
            print(f"files processed: {processed_files}. Conversion of .csv to MIDI files in {pathname} has terminated")
            break


if __name__ == '__main__':
    main_loop()
