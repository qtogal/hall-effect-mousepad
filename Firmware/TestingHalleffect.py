import time
import analogio
import digitalio
import board

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
        sensor_map[mux0_sensor_map[i][3]][mux0_sensor_map[i][2]] = abs(adc[mux0_sensor_map[i][1]].value)
        sensor_map[mux1_sensor_map[i][3]][mux1_sensor_map[i][2]] = abs(adc[mux1_sensor_map[i][1]].value)
        sensor_map[mux2_sensor_map[i][3]][mux2_sensor_map[i][2]] = abs(adc[mux2_sensor_map[i][1]].value)
    
#actual code for mouse detection

#constants
noise = 300                             # per sensor adc count jitter range
lift = 3000                             # adc value maximum before considering lifted
dpi = 20                                # scaling movement distance
wait = 0.001                            # delay set for mux to settle
calibration_frames = 20                 # initial sensor calibration frames

# Calibrate sensor readings by taking an average over 20 frames

for _ in range(calibration_frames):
    read_all()
    for i in range(MUX):
        for j in range(N/MUX):
            baseline_sensor[i][j] += sensor_map[i][j]
    
for i in range(MUX):
    for j in range(N/MUX):
        baseline_sensor[i][j]/calibration_frames

ini_x = 0
ini_y = 0


while True:

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
    
    if total > lift:
        
