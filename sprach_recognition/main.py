# importing libraries
import speech_recognition as sr

import os

from pydub import AudioSegment
from pydub.silence import split_on_silence


# a function that splits the audio file into chunks
# and applies speech recognition
def silence_based_conversion(wav_path, txt_path, chunk_dir):
    # open the audio file stored in
    # the local system as a wav file.

    print(f"processing {wav_path}")
    song = AudioSegment.from_wav(wav_path)

    # open a file where we will concatenate
    # and store the recognized text
    fh = open(txt_path, "w+")

    # split track where silence is 0.5 seconds
    # or more and get chunks
    chunks = split_on_silence(song,
                              # must be silent for at least 0.5 seconds
                              # or 500 ms. adjust this value based on user
                              # requirement. if the speaker stays silent for
                              # longer, increase this value. else, decrease it.
                              min_silence_len=800,

                              # consider it silent if quieter than -30 dBFS
                              # adjust this per requirement
                              silence_thresh=-42
                              )

    # create a directory to store the audio chunks.
    try:
        os.mkdir(chunk_dir)
    except FileExistsError:
        pass

    # move into the directory to
    # store the audio files.
    os.chdir(chunk_dir)

    i = 0
    # process each chunk
    for chunk in chunks:

        # Create 0.5 seconds silence chunk
        chunk_silent = AudioSegment.silent(duration=500)

        # add 0.5 sec silence to beginning and
        # end of audio chunk. This is done so that
        # it doesn't seem abruptly sliced.
        audio_chunk = chunk_silent + chunk + chunk_silent

        # export audio chunk and save it in
        # the current directory.
        print(f"saving chunk{0}.wav")
        # specify the bitrate to be 192 k
        audio_chunk.export("./chunk{0}.wav".format(i), bitrate='192k', format="wav")

        # the name of the newly created chunk
        filename = 'chunk' + str(i) + '.wav'

        print("Processing chunk " + str(i))

        # get the name of the newly created chunk
        # in the AUDIO_FILE variable for later use.
        file = filename

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
            rec = r.recognize_google(audio_listened, language="de-DE")
            # write the output to the file.
            fh.write(rec + "\n")

        # catch any errors.
        except sr.UnknownValueError:
            print("Could not understand audio")

        except sr.RequestError as e:
            print("Could not request results. check your internet connection")

        i += 1

    os.chdir('..')

    for chunk_file in os.listdir(chunk_dir):
        chunk_file_path = os.path.join(chunk_dir, chunk_file)
        print(f"deleting {chunk_file_path}")
        os.remove(chunk_file_path)


if __name__ == '__main__':
    wav_directory = 'wav_files'
    txt_directory = 'txt_files'
    chunk_directory = 'audio_chunks'
    for path in os.listdir(wav_directory):
        file_name = os.path.splitext(path)
        wav_name = os.path.join(wav_directory, path)
        txt_name = os.path.join(txt_directory, file_name[0] + '.txt')
        silence_based_conversion(wav_name, txt_name, chunk_directory)
