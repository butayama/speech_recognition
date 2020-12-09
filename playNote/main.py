# This is a sample Python script.

from music import *


def play_note(pitch, duration):
    print(f'Note: {pitch}, {duration}')
    Play.midi(note)


if __name__ == '__main__':
    tonhoehe = 'C4'
    dauer = 'HN'
    note = Note(tonhoehe, dauer)
    play_note(note)


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
