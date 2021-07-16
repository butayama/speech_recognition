# importing libraries
import speech_recognition as sr

import os

from pydub import AudioSegment
from pydub.silence import split_on_silence


def process_chunks(chunk_dir='audio_chunks', filename='u_01.wav'):
    # move into the directory to
    # store the audio files.
    os.chdir(chunk_dir)
    # process chunk
    file = filename
    # open a file where we will concatenate
    # and store the recognized text
    fh = open("recognized.txt", "w+")

    # create a speech recognition object
    r = sr.Recognizer()

    # recognize the chunk
    with sr.AudioFile(file) as source:
        # remove this if it is not working
        # correctly.
        r.adjust_for_ambient_noise(source)
        audio_listened = r.listen(source)

    try:
        # try converting it to text
        rec = r.recognize_google(audio_listened)
        # write the output to the file.
        fh.write(rec + ". ")

    # catch any errors.
    except sr.UnknownValueError:
        print("Could not understand audio")

    except sr.RequestError as e:
        print(e, "Could not request results. check your internet connection")
    os.chdir('..')


if __name__ == '__main__':
    process_chunks()
