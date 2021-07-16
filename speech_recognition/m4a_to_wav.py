# m4a_to_wav.py
# source: https://gist.github.com/arjunsharma97/0ecac61da2937ec52baf61af1aa1b759

# Packages reqd: pydub, ffmpeg

# pydub - pip install pydub

# ffmpeg:
# sudo add-apt-repository ppa:kirillshkrogalev/ffmpeg-next
# sudo apt-get update
# sudo apt-get install ffmpeg

# Load the m4a files (in M4a_files.tar.gz)

# !tar - xvzf
# M4a_files.tar.gz

# Delete unwanted files (here: Tapping files)

# !find
# M4a_files / -name
# 'tapping_results.*' - delete

# Converting to wav
# Using pydub

# Convert all file extensions to m4a (if required)

import os
from pydub import AudioSegment

folder = 'M4a_files/'
for filename in os.listdir(folder):
    # noinspection SpellCheckingInspection
    infilename = os.path.join(folder, filename)
    if not os.path.isfile(infilename):
        continue
    # noinspection SpellCheckingInspection
    oldbase = os.path.splitext(filename)
    # noinspection SpellCheckingInspection
    newname = infilename.replace('.tmp', '.m4a')
    os.rename(infilename, newname)

# Convert m4a extension files to wav extension files

formats_to_convert = ['.m4a']

for (dirpath, dirnames, filenames) in os.walk("M4a_files/"):
    for filename in filenames:
        if filename.endswith(tuple(formats_to_convert)):

            filepath = dirpath + '/' + filename
            (path, file_extension) = os.path.splitext(filepath)
            file_extension_final = file_extension.replace('.', '')
            try:
                track = AudioSegment.from_file(filepath,
                                               file_extension_final)
                wav_filename = filename.replace(file_extension_final, 'wav')
                wav_path = dirpath + '/' + wav_filename
                print('CONVERTING: ' + str(filepath))
                file_handle = track.export(wav_path, format='wav')
                os.remove(filepath)
            except IOError:
                print("ERROR CONVERTING " + str(filepath))

# Rename folder M4a_files as wav_files
