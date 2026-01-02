import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import io

# --- INPUT PARAMETERS ---
diameter = 30                   # outer diameter [mm]
height = 30                     # container height [mm]
center_fill_amount = 2.5        # how tightly to fill the center
line_width = 2.5                # line width [mm]
first_layer_line_width = 2.5    # first layer line width [mm]
layer_height = 1.0              # layer height [mm]
first_layer_height = 1.0        # first layer height [mm]
flow_rate = 102                 # flow rate [%]
first_layer_flow_rate = 104     # first layer flow rate [%]
flow_limit = 15                 # max volumetric flow [mm^3/s]
velocity_limit = 50             # velocity limit [mm/s]
first_layer_fan = 20            # first layer fan speed [%]
corner_fan = 80                 # corner fan speed [%]
vertical_wall_fan = 60          # vertical wall fan speed [%]
ironing_rotations = 0.0         # top ironing rotations [rev]
ironing_lift = 0.0              # ironing lift [mm]
fillet_radius = 1.5             # corner fillet radius [mm]
filament_dia = 1.75             # filament diameter [mm]
bed_temp = 65                   # bed temperature [°C]
first_layer_temp = 190          # nozzle temperature for first layer/base spiral [°C]
wall_temp = 200                 # nozzle temperature for fillet and walls [°C]

# --- SYSTEM PARAMETERS ---
center_x, center_y = 128, 128
outer_radius = diameter / 2
inner_radius = outer_radius - fillet_radius
points_per_rev = 360

START_GCODE = """
; EXECUTABLE_BLOCK_START
M73 P0 R13
M201 X12000 Y12000 Z1500 E5000
M203 X500 Y500 Z30 E30
M204 P12000 R5000 T12000
M205 X9.00 Y9.00 Z3.00 E3.00 ; sets the jerk limits, mm/sec
; FEATURE: Custom
;===== machine: A1 =========================
G392 S0
M9833.2
;M400
;M73 P1.717

;===== start to heat heatbead&hotend==========
M1002 gcode_claim_action : 2
M1002 set_filament_type:PLA
M104 S140
M140 S65

;=====avoid end stop =================
G91
G380 S2 Z40 F1200
G380 S3 Z-15 F1200
G90

;===== reset machine status =================
;M290 X39 Y39 Z8
M204 S6000

M630 S0 P0
G91
M17 Z0.3 ; lower the z-motor current

G90
M17 X0.65 Y1.2 Z0.6 ; reset motor current to default
M960 S5 P1 ; turn on logo lamp
G90
M220 S100 ;Reset Feedrate
M221 S100 ;Reset Flowrate
M73.2   R1.0 ;Reset left time magnitude
;M211 X0 Y0 Z0 ; turn off soft endstop to prevent protential logic problem

;====== cog noise reduction=================
M982.2 S1 ; turn on cog noise reduction

M1002 gcode_claim_action : 13

G28 X
G91
G1 Z5 F1200
G90
G0 X128 F30000
G0 Y254 F3000
G91
G1 Z-5 F1200

M109 S25 H140

M17 E0.3
M83
G1 E10 F1200
G1 E-0.5 F30
M17 D

G28 Z P0 T140; home z with low precision,permit 300deg temperature
M104 S200

M1002 judge_flag build_plate_detect_flag
M622 S1
  G39.4
  G90
  G1 Z5 F1200
M623

;M400
;M73 P1.717

;===== prepare print temperature and material ==========
M1002 gcode_claim_action : 24

M400
;G392 S1
M211 X0 Y0 Z0 ;turn off soft endstop
M975 S1 ; turn on

G90
G1 X-28.5 F30000
G1 X-48.2 F3000

M620 M ;enable remap
M620 S0A   ; switch material if AMS exist
    M1002 gcode_claim_action : 4
    M400
    M1002 set_filament_type:UNKNOWN
    M109 S200
    M104 S250
    M400
    T0
    G1 X-48.2 F3000
M73 P1 R13
    M400

    M620.1 E F374.174 T240
    M109 S250 ;set nozzle to common flush temp
    M106 P1 S0
    G92 E0
    G1 E50 F200
    M400
    M1002 set_filament_type:PLA
M621 S0A

M109 S240 H300
G92 E0
G1 E50 F200 ; lower extrusion speed to avoid clog
M73 P2 R13
M400
M106 P1 S178
G92 E0
G1 E5 F200
M73 P4 R13
M104 S200
G92 E0
G1 E-0.5 F300

G1 X-28.5 F30000
G1 X-48.2 F3000
G1 X-28.5 F30000 ;wipe and shake
G1 X-48.2 F3000
G1 X-28.5 F30000 ;wipe and shake
M73 P5 R12
G1 X-48.2 F3000

;G392 S0

M400
M106 P1 S0
;===== prepare print temperature and material end =====

;M400
;M73 P1.717

;===== auto extrude cali start =========================
M975 S1
;G392 S1

G90
M83
T1000
G1 X-48.2 Y0 Z10 F10000
M400
M1002 set_filament_type:UNKNOWN

M412 S1 ;  ===turn on  filament runout detection===
M400 P10
M620.3 W1; === turn on filament tangle detection===
M400 S2

M1002 set_filament_type:PLA

;M1002 set_flag extrude_cali_flag=1
M1002 judge_flag extrude_cali_flag

M622 J1
    M1002 gcode_claim_action : 8

    M109 S200
    G1 E10 F375
    M983 F6.25 A0.3 H2; cali dynamic extrusion compensation

    M106 P1 S255
    M400 S5
    G1 X-28.5 F18000
M73 P6 R12
    G1 X-48.2 F3000
    G1 X-28.5 F18000 ;wipe and shake
    G1 X-48.2 F3000
    G1 X-28.5 F12000 ;wipe and shake
    G1 X-48.2 F3000
    M400
    M106 P1 S0

    M1002 judge_last_extrude_cali_success
    M622 J0
        M983 F6.25 A0.3 H2; cali dynamic extrusion compensation
        M106 P1 S255
        M400 S5
        G1 X-28.5 F18000
        G1 X-48.2 F3000
M73 P7 R12
        G1 X-28.5 F18000 ;wipe and shake
        G1 X-48.2 F3000
        G1 X-28.5 F12000 ;wipe and shake
        M400
        M106 P1 S0
    M623
    
    G1 X-48.2 F3000
    M400
    M984 A0.1 E1 S1 F6.25 H2
    M106 P1 S178
    M400 S7
    G1 X-28.5 F18000
    G1 X-48.2 F3000
M73 P39 R8
    G1 X-28.5 F18000 ;wipe and shake
    G1 X-48.2 F3000
    G1 X-28.5 F12000 ;wipe and shake
    G1 X-48.2 F3000
    M400
    M106 P1 S0
M623 ; end of "draw extrinsic para cali paint"

;G392 S0
;===== auto extrude cali end ========================

;M400
;M73 P1.717

M104 S170 ; prepare to wipe nozzle
M106 S255 ; turn on fan

;M400
;M73 P1.717

;===== wipe nozzle ===============================
M1002 gcode_claim_action : 14

M975 S1
M106 S255 ; turn on fan (G28 has turn off fan)
M211 S; push soft endstop status
M211 X0 Y0 Z0 ;turn off Z axis endstop

;===== remove waste by touching start =====

M104 S170 ; set temp down to heatbed acceptable

M83
G1 E-1 F500
G90
M83

M109 S170
G0 X108 Y-0.5 F30000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X110 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X112 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X114 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X116 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X118 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X120 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X122 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X124 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X126 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X128 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X130 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X132 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X134 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X136 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X138 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X140 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X142 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X144 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X146 F10000
G380 S3 Z-5 F1200
G1 Z2 F1200
G1 X148 F10000
G380 S3 Z-5 F1200

G1 Z5 F30000
;===== remove waste by touching end =====

G1 Z10 F1200
G0 X118 Y261 F30000
G1 Z5 F1200
M109 S150

G28 Z P0 T300; home z with low precision,permit 300deg temperature
G29.2 S0 ; turn off ABL
M104 S140 ; prepare to abl
G0 Z5 F20000

G0 X128 Y261 F20000  ; move to exposed steel surface
G0 Z-1.01 F1200      ; stop the nozzle

G91
G2 I1 J0 X2 Y0 F2000.1
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5

G90
G1 Z10 F1200

;===== brush material wipe nozzle =====

G90
G1 Y250 F30000
G1 X55
G1 Z1.300 F1200
G1 Y262.5 F6000
G91
G1 X-35 F30000
G1 Y-0.5
G1 X45
G1 Y-0.5
G1 X-45
G1 Y-0.5
M73 P40 R8
G1 X45
G1 Y-0.5
G1 X-45
G1 Y-0.5
G1 X45
G1 Z5.000 F1200

G90
G1 X30 Y250.000 F30000
G1 Z1.300 F1200
G1 Y262.5 F6000
G91
G1 X35 F30000
G1 Y-0.5
G1 X-45
G1 Y-0.5
G1 X45
G1 Y-0.5
G1 X-45
G1 Y-0.5
G1 X45
G1 Y-0.5
G1 X-45
G1 Z10.000 F1200

;===== brush material wipe nozzle end =====

G90
;G0 X128 Y261 F20000  ; move to exposed steel surface
G1 Y250 F30000
G1 X138
G1 Y261
G0 Z-1.01 F1200      ; stop the nozzle

G91
G2 I1 J0 X2 Y0 F2000.1
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5
G2 I1 J0 X2
G2 I-0.75 J0 X-1.5

M109 S140
M106 S255 ; turn on fan (G28 has turn off fan)

M211 R; pop softend status

;===== wipe nozzle end ================================

;M400
;M73 P1.717

;===== bed leveling ==================================
M1002 judge_flag g29_before_print_flag

G90
G1 Z5 F1200
G1 X0 Y0 F30000
G29.2 S1 ; turn on ABL

M190 S65; ensure bed temp
M109 S140
M106 S0 ; turn off fan , too noisy

M622 J1
    M1002 gcode_claim_action : 1
    G29 A1 X106.691 Y111.359 I55.5994 J55.5926
    M400
    M500 ; save cali data
M623
;===== bed leveling end ================================

;===== home after wipe mouth============================
M1002 judge_flag g29_before_print_flag
M622 J0

    M1002 gcode_claim_action : 13
    G28

M623

;===== home after wipe mouth end =======================

;M400
;M73 P1.717

G1 X108.000 Y-0.500 F30000
G1 Z0.300 F1200
M400
G2814 Z0.32

M104 S200 ; prepare to print

;===== extrude cali test ===============================

M400
    M900 S
    M900 C
    G90
    M83

    M109 S200
    G0 X128 E8  F900
    G0 X133 E.3742  F1500
M73 P41 R8
    G0 X138 E.3742  F6000
    G0 X143 E.3742  F1500
    G0 X148 E.3742  F6000
    G0 X153 E.3742  F1500
    G91
    G1 X1 Z-0.300
    G1 X4
    G1 Z1 F1200
    G90
    M400

M900 R

M1002 judge_flag extrude_cali_flag
M622 J1
    G90
    G1 X108.000 Y1.000 F30000
    G91
    G1 Z-0.700 F1200
    G90
    M83
    G0 X128 E10  F900
    G0 X133 E.3742  F1500
    G0 X138 E.3742  F6000
    G0 X143 E.3742  F1500
    G0 X148 E.3742  F6000
    G0 X153 E.3742  F1500
    G91
    G1 X1 Z-0.300
    G1 X4
    G1 Z1 F1200
    G90
    M400
M623

G1 Z0.2

;M400
;M73 P1.717

;========turn off light and wait extrude temperature =============
M1002 gcode_claim_action : 0
M400

;===== for Textured PEI Plate , lower the nozzle as the nozzle was touching topmost of the texture when homing ==
;curr_bed_type=Textured PEI Plate

G29.1 Z-0.02 ; for Textured PEI Plate


M960 S1 P0 ; turn off laser
M960 S2 P0 ; turn off laser
M106 S0 ; turn off fan
M106 P2 S0 ; turn off big fan
M106 P3 S0 ; turn off chamber fan

M975 S1 ; turn on mech mode supression
G90
M83
T1000

M211 X0 Y0 Z0 ;turn off soft endstop
;G392 S1 ; turn on clog detection
M1007 S1 ; turn on mass estimation
G21
G90
M83

M204 S500
G1 E-0.8 F1800 ; retract
G1 Z5 F12000
"""

END_GCODE = """
; move to safe Z height
G91
G1 Z20 F1200
G90

G392 S0 ;turn off nozzle clog detect

M400 ; wait for buffer to clear
G92 E0 ; zero the extruder
G1 E-0.8 F1800 ; retract
G1 X-13.0 F3000 ; move to safe pos

M140 S0 ; turn off bed
M106 S0 ; turn off fan
M106 P2 S0 ; turn off remote part cooling fan
M106 P3 S0 ; turn off chamber cooling fan

;G1 X27 F15000 ; wipe

M104 S0 ; turn off hotend

M400 ; wait all motion done
M17 S
M17 Z0.4 ; lower z motor current to reduce impact if there is something in the bottom

    G1 Z111.2 F600
    G1 Z109.2
M73 P99 R0

M400 P100
M17 R ; restore z current

G90
G1 X-48 Y180 F3600
M73 P100 R0

M220 S100  ; Reset feedrate magnitude
M201.2 K1.0 ; Reset acc magnitude
M73.2   R1.0 ;Reset left time magnitude
M1002 set_gcode_claim_speed_level : 0

;M17 X0.8 Y0.8 Z0.5 ; lower motor current to 45% power
M400
M18 X Y Z

M73 P100 R0
; EXECUTABLE_BLOCK_END
"""

# --- 0. VELOCITY & FLOW CALCULATIONS ---
def get_area_bead(w, h):
    return ((w - h) * h) + (np.pi * (h / 2)**2)

area_base_geo = get_area_bead(first_layer_line_width, first_layer_height)
area_rest_geo = get_area_bead(line_width, layer_height)

area_base_effective = area_base_geo * (first_layer_flow_rate / 100.0)
area_rest_effective = area_rest_geo * (flow_rate / 100.0)

first_layer_velocity = flow_limit / area_base_effective
wall_velocity = flow_limit / area_rest_effective

velocity = min(first_layer_velocity, wall_velocity)

if velocity > velocity_limit:
    print(f"WARNING: Calculated speed {velocity:.1f} mm/s exceeds velocity_limit {velocity_limit} mm/s")
    print("Recalculating with reduced volumetric flow limit...")
    
    flow_limit = velocity_limit * min(area_base_effective, area_rest_effective)
    
    first_layer_velocity = flow_limit / area_base_effective
    wall_velocity = flow_limit / area_rest_effective
    velocity = min(first_layer_velocity, wall_velocity)
    
    print(f"New volumetric flow limit: {flow_limit:.2f} mm³/s")
    print(f"New speed: {velocity:.1f} mm/s")

feedrate = velocity * 60

# --- 1. E-STEP CALCULATIONS ---
area_filament = np.pi * (filament_dia / 2)**2
e_per_mm_base = area_base_effective / area_filament * first_layer_flow_rate / 100.0
e_per_mm_rest = area_rest_effective / area_filament * flow_rate / 100.0
e_center_fill = center_fill_amount / area_filament

# --- 2. PATH GENERATION ---
buffer = io.StringIO()
X, Y, Z = [], [], []
last_fan = 0

buffer.write("; Custom spiral container G-code generator by Stijns Projects\n")
buffer.write(START_GCODE)
buffer.write(f"G1 F{int(feedrate)}\n")
buffer.write(f"M109 S{first_layer_temp} ; set nozzle temp for first layer\n")
buffer.write(f"M190 S{bed_temp} ; set bed temp\n")

# Start exactly at center
nx_start, ny_start, nz_start = center_x, center_y, first_layer_height

buffer.write(f"G0 X{nx_start:.3f} Y{ny_start:.3f} Z{nz_start:.3f} F5000 ; move to center\n")
buffer.write(f"G1 E0.8 F1800 ; unretract\n") 

if center_fill_amount > 0:
    buffer.write(f"G1 E{e_center_fill:.5f} F300 ; deposit center fill amount slowly\n")
    buffer.write(f"G4 P100 ; dwell 0.5s to let pressure equalize\n")

buffer.write(f"G1 F{int(feedrate)}\n")

X.append(nx_start); Y.append(ny_start); Z.append(nz_start)

# --- BASE SPIRAL ---
num_base_revs = inner_radius / first_layer_line_width
base_steps = int(num_base_revs * points_per_rev)
for i in range(1, base_steps + 1):
    p = i / base_steps
    r = p * inner_radius
    theta = p * num_base_revs * 2 * np.pi
    
    nx = center_x + r * np.cos(theta)
    ny = center_y + r * np.sin(theta)
    nz = first_layer_height
    
    dist = np.sqrt((nx-X[-1])**2 + (ny-Y[-1])**2 + (nz-Z[-1])**2)
    
    # Standard flow calculation
    buffer.write(f"G1 X{nx:.3f} Y{ny:.3f} Z{nz:.3f} E{dist * e_per_mm_base:.5f}\n")
    
    # Fan Logic
    fan_val = int(p * first_layer_fan)
    if abs(fan_val - last_fan) > 5:
        buffer.write(f"M106 S{int(fan_val * 255 / 100)}\n")
        last_fan = fan_val
        
    X.append(nx); Y.append(ny); Z.append(nz)

buffer.write(f"M104 S{wall_temp}\n")

# --- FILLET ---
curr_theta = theta
fillet_revs = fillet_radius / layer_height
fillet_steps = int(fillet_revs * points_per_rev)
for i in range(1, fillet_steps + 1):
    p = i / fillet_steps
    phi = p * (np.pi / 2)
    r = inner_radius + (fillet_radius * np.sin(phi))
    nz = first_layer_height + (fillet_radius * (1 - np.cos(phi)))
    t = curr_theta + (p * fillet_revs * 2 * np.pi)
    nx, ny = center_x + r * np.cos(t), center_y + r * np.sin(t)
    
    dist = np.sqrt((nx-X[-1])**2 + (ny-Y[-1])**2 + (nz-Z[-1])**2)
    buffer.write(f"G1 X{nx:.3f} Y{ny:.3f} Z{nz:.3f} E{dist * e_per_mm_rest:.5f}\n")
    
    fan_val = int(first_layer_fan + (corner_fan - first_layer_fan) * p)
    if abs(fan_val - last_fan) > 5:
        buffer.write(f"M106 S{int(fan_val * 255 / 100)}\n")
        last_fan = fan_val
    
    X.append(nx); Y.append(ny); Z.append(nz)

# --- VERTICAL WALL ---
curr_theta = t
remaining_height = height - Z[-1]
wall_revs = remaining_height / layer_height
wall_steps = int(wall_revs * points_per_rev)
z_start = Z[-1]
for i in range(1, wall_steps + 1):
    p = i / wall_steps
    nz = z_start + (p * remaining_height)
    t = curr_theta + (p * wall_revs * 2 * np.pi)
    nx, ny = center_x + outer_radius * np.cos(t), center_y + outer_radius * np.sin(t)
    
    dist = np.sqrt((nx-X[-1])**2 + (ny-Y[-1])**2 + (nz-Z[-1])**2)
    buffer.write(f"G1 X{nx:.3f} Y{ny:.3f} Z{nz:.3f} E{dist * e_per_mm_rest:.5f}\n")
    
    fan_val = int(corner_fan + (vertical_wall_fan - corner_fan) * p)
    if abs(fan_val - last_fan) > 5:
        buffer.write(f"M106 S{int(fan_val * 255 / 100)}\n")
        last_fan = fan_val

    X.append(nx); Y.append(ny); Z.append(nz)

# --- TOP CLOSURE ---
curr_theta = t
final_z = Z[-1]
for i in range(1, points_per_rev + 1):
    p = i / points_per_rev
    t = curr_theta + (p * 2 * np.pi)
    nx, ny = center_x + outer_radius * np.cos(t), center_y + outer_radius * np.sin(t)
    dist = np.sqrt((nx-X[-1])**2 + (ny-Y[-1])**2)
    ramp = 1.0 - (0.95 * (p ** 1.5))
    buffer.write(f"G1 X{nx:.3f} Y{ny:.3f} Z{final_z:.3f} E{dist * e_per_mm_rest * ramp:.5f}\n")
    X.append(nx); Y.append(ny); Z.append(final_z)

# --- IRONING ---
curr_theta_after_closure = curr_theta + (2 * np.pi)
ironing_steps = int(points_per_rev * ironing_rotations)
for i in range(1, ironing_steps + 1):
    p = i / ironing_steps 
    t = curr_theta_after_closure + (p * ironing_rotations * 2 * np.pi)
    nx, ny = center_x + outer_radius * np.cos(t), center_y + outer_radius * np.sin(t)
    nz = final_z + (ironing_lift * p)
    buffer.write(f"G1 X{nx:.3f} Y{ny:.3f} Z{nz:.3f} E0\n")
    X.append(nx); Y.append(ny); Z.append(nz)

# --- RETRACTION ---
buffer.write(f"G1 E-0.8 F1800 ; Retract filament\n")
buffer.write(f"G1 F{int(feedrate)} ; Reset to print speed\n\n")

buffer.write(END_GCODE)

# --- 3. VISUALIZATION ---
ax = plt.figure().add_subplot(projection='3d')
ax.plot(X, Y, Z, lw=0.5)
ax.set_box_aspect([1, 1, (max(Z))/(diameter)])
ax.set_xlabel("X [mm]"); ax.set_ylabel("Y [mm]"); ax.set_zlabel("Z [mm]")
plt.show()

# --- 4. EXPORT DIALOG ---
root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
file_path = filedialog.asksaveasfilename(
    defaultextension=".gcode",
    filetypes=[("G-code files", "*.gcode")],
    initialfile="spiral_container.gcode"
)

if file_path:
    with open(file_path, "w") as f:
        f.write(buffer.getvalue())
    print(f"File saved successfully at: {file_path}")
else:
    print("Save cancelled.")

buffer.close()
root.destroy()

# --- 5. STATS ---
total_length = 0
for i in range(1, len(X)):
    total_length += np.sqrt((X[i]-X[i-1])**2 + (Y[i]-Y[i-1])**2 + (Z[i]-Z[i-1])**2)

total_filament = 0
for i in range(1, len(X)):
    dist = np.sqrt((X[i]-X[i-1])**2 + (Y[i]-Y[i-1])**2 + (Z[i]-Z[i-1])**2)
    if Z[i] <= first_layer_height + 0.01:
        total_filament += dist * e_per_mm_base
    else:
        total_filament += dist * e_per_mm_rest

print(f"Print time estimate: {total_length / velocity / 60:.1f} minutes")
print(f"Velocity: {velocity:.1f} mm/s")
print(f"Total filament used: {total_filament:.1f} mm")
