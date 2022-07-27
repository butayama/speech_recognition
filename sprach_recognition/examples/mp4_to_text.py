from urllib.request import urlopen
import speech_recognition as sr
import subprocess
import os

def speech_to_text():

    testfile = 'Ellen 220610 0755.m4a'
    mp4file = testfile

    with open("test.mp4", "wb") as handle:
        handle.write(mp4file.read())

    cmdline = ['avconv',
               '-i',
               'test.mp4',
               '-vn',
               '-f',
               'wav',
               'test.wav']
    subprocess.call(cmdline)

    r = sr.Recognizer()
    with sr.AudioFile('test.wav') as source:
        audio = r.record(source)

    command = r.recognize_google(audio)
    print(command)

    os.remove("test.mp4")
    os.remove("test.wav")

if __name__ == "__main__":
    speech_to_text()

# import requests
# import sprach_recognition as sr
# from converter import Converter
#
# url = 'https://cdn.fbsbx.com/v/t59.3654-21/15720510_10211855778255994_5430581267814940672_n.mp4/audioclip-1484407992000-3392.mp4?oh=a78286aa96c9dea29e5d07854194801c&oe=587C3833'
# r = requests.get(url)
# c = Converter()
#
# with open("/tmp/test.mp4", "wb") as handle:
#     for data in r.iter_content():
#         handle.write(data)
#
# conv = c.convert('/tmp/test.mp4', '/tmp/test.wav', {
#     'format': 'wav',
#     'audio': {
#     'codec': 'pcm',
#     'samplerate': 44100,
#     'channels': 2
#     },
# })
#
# for timecode in conv:
#     pass
#
# r = sr.Recognizer()
# with sr.AudioFile('/tmp/test.wav') as source:
#     audio = r.record(source)
#
# command = r.recognize_google(audio)
# print command