import tloen
import asyncio
import supriya

app = tloen.Application()


async def start_example():
    context = await app.add_context()
    track = context.add_track()
    instrument = track.add_device(tloen.domain.Instrument)
    app.boot()
    print(context.query())
    scene = app.add_scene()

    clip = track.slots[0].add_clip(notes=[
        tloen.domain.Note(0, 0.25, pitch=64),
        tloen.domain.Note(0.5, 0.75, pitch=67),
    ])
    track.slots[0].fire()
    print("example runs")
    go_on = True
    while go_on:
        inp = input("s = stop")
        if inp == "s" or inp == "S":
            go_on = False
    track.stop()


if __name__ == "__main__":

    start_example()


