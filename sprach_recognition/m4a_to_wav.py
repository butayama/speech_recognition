# https://www.tutorialexample.com/converting-m4a-to-wav-using-pydub-in-python-python-tutorial/
# Conversion mit .m4a Dateien funktioniert nicht. --> ffmpeg Fehler!
# Stattdessen online convertieren funktioniert: https://m4atowav.com/#start
# mp4 und mp3 nach wav funktioniert!

from pydub import AudioSegment

m4a_file = 'Ellen_220727_10.08.mp4'
wav_filename = r"test_01.wav"
track = AudioSegment.from_file(m4a_file, format='mp4')
file_handle = track.export(wav_filename, format='wav')
