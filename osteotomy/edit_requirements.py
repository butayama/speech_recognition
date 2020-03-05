# get all modules without version numbers from a requirements.txt file
from os import access, R_OK, W_OK
from os.path import exists, join, dirname
from shutil import copy2


def overwrite_file(filename):
    """loop until overwrite existing file or input of a new filename is true"""
    dump_file = False
    while not dump_file:
        if exists(filename):
            overwrite = input(f"overwrite {filename} (y/n): ")
            if overwrite in ["y", "Y"]:
                dump_file = True
            if overwrite in ["n", "N"]:
                new_name = input(f"new filename: ")
                filename = join(dirname(filename), new_name)
                print(filename)
        else:
            dump_file = True

    return filename


def strip_version_numbers(f='requirements.txt', f_old='requirements_old.txt'):
    if access(f, R_OK and W_OK):
        try:
            overwrite_file(f_old)
            copy2(f, f_old)
        except IOError:
            print(f"file {f} could not be copied to {f_old} ")
    else:
        print(f"file {f} is not accessible for read or write operations.")
    with open(f, 'w') as file_out:
        with open(f_old) as file_object:
            for line in file_object:
                module_name = line.split('=')
                file_out.write(f"{module_name[0]}\n")


if __name__ == "__main__":
    strip_version_numbers()
