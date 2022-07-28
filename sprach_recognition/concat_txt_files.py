import os
import glob


def concat_files(directory):
    read_files = glob.glob(directory + '\\*.txt')
    with open("result.txt", "wb") as outfile:
        for f in read_files:
            with open(f, "rb") as infile:
                outfile.write("====================================================")
                outfile.write(f)
                outfile.write("====================================================")
                outfile.write(infile.read())


if __name__ == '__main__':
    txt_directory = 'test_txt_files'

    for path in os.listdir(txt_directory):
        concat_files(txt_directory)
