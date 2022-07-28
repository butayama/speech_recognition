# https://www.tutorialexample.com/converting-m4a-to-wav-using-pydub-in-python-python-tutorial/

from pydub import AudioSegment

m4a_file = 'test_01.m4a'
wav_filename = r"test_01.wav"
track = AudioSegment.from_file(m4a_file, format='m4a')
file_handle = track.export(wav_filename, format='wav')
