import time
import board
import analogio
import digitalio
import usb_hid
from adafruit_hid.mouse import Mouse

COLS = 6
ROWS = 4
MUX = 3
row_spacing = 16.6
col_spacing = 15.3

N = COLS*ROWS

select = []

for i in (board.GP10, board.GP11, board.GP12, board.GP13):
    pin = digitalio.DigitalInOut(i)
    pin.direction = digitalio.Direction.OUTPUT
    select.append(pin)

adc = [
    analogio.AnalogIn(board.A0),
    analogio.AnalogIn(board.A1),
    analogio.AnalogIn(board.A2),
]

mouse = Mouse(usb_hid.devices)

#Make the mapping of the sensor layout based on the pins connected to each sensor, (ch, x, y)
mux0_sensor_map = [
    (0,0,3), (1,0,2), (2,0,1), (3,0,0), (4,1,3), (5,1,2), (6,1,1), (7,1,0)
]

mux1_sensor_map = [
    (0,2,3), (1,2,2), (2,2,1), (3,2,0), (4,3,3), (5,3,2), (6,3,1), (7,3,0)
]

mux2_sensor_map = [
    (0,4,3), (1,4,2), (2,4,1), (3,4,0), (4,5,3), (5,5,2), (6,5,1), (7,5,0)
]

mux_map = [mux0_sensor_map, mux1_sensor_map, mux2_sensor_map]

sensor_map = [
    [0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0],          
]

baseline_sensor = sensor_map

using_map = [
    [0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0],          
]

def set_channel(ch):
    for i, pin in enumerate(select):
        pin.value = bool((ch >>i )&1)

def read_all():
    for i in range(8):
        set_channel(i)
        sensor_map[mux0_sensor_map[i][2]][mux0_sensor_map[i][1]] = abs(adc[mux0_sensor_map[i][0]].value)
        sensor_map[mux1_sensor_map[i][2]][mux1_sensor_map[i][1]] = abs(adc[mux1_sensor_map[i][0]].value)
        sensor_map[mux2_sensor_map[i][2]][mux2_sensor_map[i][1]] = abs(adc[mux2_sensor_map[i][0]].value)
    
#actual code for mouse detection

#constants
noise = 300                             # per sensor adc count jitter range
lift = 3000                             # adc value maximum before considering lifted
dpi = 20                                # scaling movement distance
wait = 0.001                            # delay set for mux to settle
calibration_frames = 20                 # initial sensor calibration frames
smooth = 0.5                            # fraction of change in x and y recorded as movement
delay = 0.25
click_ratio = 1.5

# Calibrate sensor readings by taking an average over 20 frames

for _ in range(calibration_frames):
    read_all()
    for i in range(MUX):
        for j in range(N/MUX):
            baseline_sensor[i][j] += sensor_map[i][j]
    
for i in range(MUX):
    for j in range(N/MUX):
        baseline_sensor[i][j]/calibration_frames

prev_cx = None       # previous frame position
prev_cy = None
smooth_cx = None     # low-pass-filtered cursor position
smooth_cy = None
rem_x = 0.0          # carry sub-pixel remainders
rem_y = 0.0
hover_peak = None    # the resting field strength while just hovering
clicking = False     # if button is pressed
settle_until = 0.0   # clicks don't activate until this time after the magnet lands

while True:
    now = time.monotonic()
    sx = 0.0
    sy = 0.0
    total = 0
    peak = 0

    read_all()
    for i in range(MUX):
        for j in range(N/MUX):
            w = sensor_map[i][j] - baseline_sensor[i][j]
            if w>noise:
                x = mux_map[i][j][2]
                y = mux_map[i][j][3]
                sx += w*x
                sy += w*y
                total += w
                if w> peak: 
                    peak = w
    if total > LIFT:   #weighted average
        cx = sx/total
        cy = sy/total
        if smooth_cx is None:  #record cx and cy as smooth_cx and smooth_cy if they don't have any values stored
            smooth_cx = cx
            smooth_cy = cy
        else:
            smooth_cx += (cx - smooth_cx)*smooth
            smooth_cy += (cy - smooth_cy)*smooth
        if prev_cx is None:   #No previous position is recorded
            prev_cx = smooth_cx
            prev_cy = smooth_cy
            rem_x = 0.0
            rem_y = 0.0
        else:
            dx = (smooth_cx - prev_cx)*dpi + rem_x
            dy = (smooth_cy - prev_cy)*dpi + rem_y
            ix = int(dx)
            iy = int(dy)
            rem_x = dx - ix
            rem_y = dy - iy
            if ix != 0 or iy != 0:
                mouse.move(x=ix, y=iy)
            prev_cx = smooth_cx
            prev_cy = smooth_cy

        if hover_peak is None:
            hover_peak = peak
            settle_until = now + delay
        if now<settle_until:
            hover_peak = peak
        elif not clicking:
            if peak > hover_peak*click_ratio:
                mouse.press(Mouse.LEFT_BUTTON)
                clicking = True
        else:
            if peak<hover_peak*1.1:
                mouse.release(Mouse.LEFT_BUTTON)
                clicking = False
    else:
        prev_cx = None       
        prev_cy = None
        smooth_cx = None     
        smooth_cy = None
        hover_peak = None  






    


