import time
import analogio
import digitalio
import board

select = []
muxselect = []

for i in (board.GP10, board.GP11, board.GP12, board.GP13):
    pin = digitalio.DigitalInOut(i)
    pin.direction = digitalio.Direction.OUTPUT
    select.append(pin)

def choose_channel(ch):
    for i, pin in enumerate(select):
        