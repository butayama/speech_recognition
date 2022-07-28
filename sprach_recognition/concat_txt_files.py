import os
import glob


def concat_files_binary(directory):
    read_files = glob.glob(directory + '\\*.txt')
    with open("result.txt", "wb") as outfile:
        for f in read_files:
            with open(f, "rb") as infile:
                outfile.write(infile.read())


def concat_files_txt(directory):
    read_files = glob.glob(directory + '\\*.txt')
    with open("result.txt", "wb") as outfile:
        for f in read_files:
            with open(f, "rb") as infile:
                outfile.write(f.encode(encoding='utf_8'))
                outfile.write("\n".encode(encoding='utf_8'))
                for line in infile:
                    outfile.write(line)
                    # outfile.write(f)
                    # outfile.write("====================================================")
                    outfile.write("\n".encode(encoding='utf_8'))


if __name__ == '__main__':
    txt_directory = 'test_txt_files'

    for path in os.listdir(txt_directory):
        concat_files_txt(txt_directory)
