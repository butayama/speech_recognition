import tloen
import asyncio
import supriya

loop = asyncio.get_event_loop()
app = tloen.Application()


def start_example():
    context = await app.add_context()
    track = await context.add_track()
    instrument = await track.add_device(tloen.domain.Instrument)
    await app.boot()
    print(await context.query())
    scene = await app.add_scene()
    clip = await track.slots[0].add_clip(notes=[
        tloen.domain.Note(0, 0.25, pitch=64),
        tloen.domain.Note(0.5, 0.75, pitch=67),
    ])
    await track.slots[0].fire()


if __name__ == "__main__":
    start_example()
    print("example runs")
    go_on = True
    while go_on:
        inp = input("s = stop")
        if inp == "s" or inp == "S":
            go_on = False
