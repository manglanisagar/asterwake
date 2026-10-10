"""Build the shared, metre-based cabin layout. +Y is up; window faces -Z."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
items = []
def box(name, position, size, material, collision=True, group="cabin", rotation=None):
    item = dict(name=name, shape="box", position=position, size=size,
                material=material, collision=collision, group=group)
    if rotation: item["rotation"] = rotation
    items.append(item)

materials = {
    "panel": {"color":[0.64,0.67,0.65], "roughness":0.64, "metalness":0.08},
    "warm_panel": {"color":[0.42,0.43,0.39], "roughness":0.73, "metalness":0.08},
    "graphite": {"color":[0.055,0.07,0.082], "roughness":0.51, "metalness":0.32},
    "metal": {"color":[0.24,0.29,0.31], "roughness":0.32, "metalness":0.78},
    "floor": {"color":[0.10,0.13,0.15], "roughness":0.83, "metalness":0.13},
    "fabric": {"color":[0.105,0.15,0.19], "roughness":0.98, "metalness":0},
    "linen": {"color":[0.61,0.57,0.46], "roughness":0.96, "metalness":0},
    "leather": {"color":[0.06,0.075,0.08], "roughness":0.82, "metalness":0},
    "amber": {"color":[0.80,0.45,0.16], "roughness":0.45, "metalness":0.1},
    "screen": {"color":[0.014,0.035,0.045], "roughness":0.25, "metalness":0.15},
    "light": {"color":[1,0.83,0.58], "roughness":0.3, "metalness":0,
              "emission":[1.0,0.74,0.40]},
    "cyan": {"color":[0.12,0.48,0.58], "roughness":0.4,"metalness":0,
             "emission":[0.035,0.25,0.32]},
}

# Floor plates, wall panels, a substantial pressure hull around a real aperture.
box("floor-base",[0,-0.12,-0.1],[6.6,0.22,7.9],"graphite")
for x in range(6):
    for z in range(8):
        box(f"deck-{x}-{z}",[-2.65+x*1.06,0.015,-3.52+z*0.99],
            [1.035,0.03,0.965],"floor")
for side in (-1,1):
    for z in range(8):
        box(f"wall-{side}-{z}",[side*3.25,1.4,-3.52+z*0.99],
            [0.14,2.8,0.975],"panel")
        box(f"base-rail-{side}-{z}",[side*3.14,0.14,-3.52+z*0.99],
            [0.09,0.15,0.975],"metal",False)
        box(f"upper-rail-{side}-{z}",[side*3.14,2.58,-3.52+z*0.99],
            [0.08,0.06,0.975],"graphite",False)
box("ceiling",[0,2.86,-0.1],[6.6,0.13,7.9],"warm_panel")
for x in (-2.7,0,2.7):
    box("ceiling-beam",[x,2.76,-0.1],[0.11,0.15,7.75],"metal",False)
for z in (-2.7,0,2.6):
    box("ceiling-lamp-housing",[0,2.74,z],[1.9,0.08,0.19],"graphite",False)
    box("ceiling-lamp",[0,2.695,z],[1.7,0.025,0.095],"light",False, "lights")

box("window-below",[0,0.41,-4.04],[6.6,0.82,0.24],"panel")
box("window-above",[0,2.69,-4.04],[6.6,0.28,0.24],"panel")
for side in (-1,1):
    box("window-side",[side*2.98,1.69,-4.04],[0.64,1.75,0.24],"panel")
    box("window-jamb",[side*2.64,1.68,-3.89],[0.15,1.76,0.25],"graphite")
for y in (0.83,2.52):
    box("window-frame",[0,y,-3.89],[5.42,0.15,0.26],"graphite")
    box("window-gasket",[0,y+(0.04 if y<1 else -0.04),-3.74],
        [5.25,0.025,0.015],"metal",False)
box("window-sill",[0,0.84,-3.76],[5.55,0.12,0.42],"metal")
box("window-shutter",[0,1.68,-4.09],[5.14,1.56,0.06],"graphite",False,"shutter")
for x in (-2.45,-1.7,-0.9,0,0.9,1.7,2.45):
    box("window-fastener",[x,0.825,-3.74],[0.035,0.035,0.018],"metal",False)
box("handrail",[0,0.58,-3.73],[4.7,0.035,0.035],"metal",False)
for x in (-2.2,2.2):
    box("handrail-mount",[x,0.58,-3.83],[0.04,0.05,0.2],"metal",False)
for i in range(13):
    box("vent-slot",[-0.55+i*0.09,0.27,-3.907],[0.045,0.14,0.012],"graphite",False)

# Bunk and built-in storage along the port wall.
box("bunk-base",[-2.47,0.31,-1.6],[1.35,0.59,2.55],"warm_panel")
box("bunk-trim",[-2.43,0.59,-1.6],[1.38,0.10,2.63],"metal")
box("mattress",[-2.43,0.73,-1.6],[1.23,0.19,2.40],"linen",False)
box("blanket",[-2.43,0.844,-1.22],[1.25,0.065,1.57],"fabric",False)
box("pillow",[-2.43,0.87,-2.50],[0.84,0.16,0.42],"linen",False)
for z in (-2.36,-1.53,-0.70):
    box("bunk-drawer",[-1.783,0.33,z],[0.025,0.36,0.77],"panel",False)
    box("drawer-pull",[-1.755,0.39,z],[0.05,0.035,0.24],"graphite",False)
box("bunk-headboard",[-2.48,1.06,-2.91],[1.30,0.64,0.065],"graphite")
box("bunk-shelf",[-2.98,1.90,-1.64],[0.41,0.065,2.5],"warm_panel",False)
box("reading-strip",[-2.93,1.855,-1.64],[0.10,0.018,2.1],"light",False,"lights")
for z in (-2.35,-1.65,-0.95):
    box("overhead-locker",[-2.95,2.28,z],[0.47,0.58,0.64],"panel")
    box("locker-handle",[-2.70,2.22,z],[0.035,0.17,0.025],"graphite",False)
for i in range(5):
    box("book",[-2.95,2.055,-2.25+i*0.12],[0.26,0.25,0.08],
        "fabric" if i%2 else "linen",False)

# Desk, chair, a believable communications display, cupboards.
box("desk-top",[2.42,0.80,-1.95],[1.42,0.085,2.33],"warm_panel")
for z in (-2.77,-1.13):
    box("desk-leg",[2.74,0.38,z],[0.10,0.76,0.11],"metal")
box("desk-drawers",[2.80,0.40,-1.25],[0.65,0.69,0.65],"panel")
for y in (0.26,0.49,0.68):
    box("desk-drawer-pull",[2.458,y,-1.25],[0.025,0.025,0.22],"graphite",False)
box("monitor-foot",[2.62,0.88,-2.30],[0.30,0.03,0.35],"metal",False)
box("monitor-neck",[2.73,1.04,-2.30],[0.055,0.32,0.055],"metal",False)
box("monitor-case",[2.76,1.27,-2.30],[0.06,0.49,0.77],"graphite",False)
box("monitor",[2.722,1.27,-2.30],[0.008,0.42,0.68],"screen",False)
for i in range(6):
    box("screen-line",[2.714,1.41-i*0.035,-2.43],[0.005,0.007,0.30],"cyan",False)
box("keyboard",[2.10,0.872,-2.3],[0.27,0.04,0.60],"graphite",False)
for i in range(3):
    box("keyboard-row",[2.01+i*0.074,0.896,-2.30],[0.033,0.007,0.52],"metal",False)
box("chair-seat",[1.62,0.49,-1.85],[0.54,0.14,0.58],"leather")
box("chair-back",[1.34,0.91,-1.85],[0.11,0.78,0.58],"leather")
box("chair-stem",[1.62,0.24,-1.85],[0.08,0.48,0.08],"metal",False)
box("chair-base",[1.62,0.07,-1.85],[0.62,0.055,0.56],"metal",False)
box("storage-port",[-2.88,1.14,1.95],[0.65,2.27,1.75],"panel")
box("storage-starboard",[2.88,1.14,1.95],[0.65,2.27,1.75],"panel")
for x in (-2.53,2.53):
    for z in (1.55,2.35):
        box("storage-handle",[x,1.18,z],[0.045,0.26,0.035],"graphite",False)
box("window-control",[2.98,1.25,-3.60],[0.12,0.33,0.21],"graphite",False)
box("control-indicator",[2.905,1.31,-3.60],[0.015,0.025,0.07],"cyan",False)

# Cabin aft wall has an actual door opening into a corridor and second room.
for x in (-2.0,2.0):
    box("aft-wall",[x,1.4,3.84],[2.6,2.8,0.16],"panel")
box("door-header",[0,2.59,3.84],[1.40,0.42,0.18],"graphite")
for x in (-0.73,0.73):
    box("door-jamb",[x,1.2,3.79],[0.10,2.40,0.19],"graphite")
box("cabin-door",[0,1.18,3.86],[1.34,2.36,0.075],"warm_panel",True,"door")
box("door-stripe",[0,1.45,3.808],[0.06,1.5,0.008],"amber",False,"door")
for z in (4.4,5.4,6.4,7.4):
    box("corridor-floor",[0,-0.08,z],[2.36,0.17,0.99],"floor",True,"corridor")
    box("corridor-ceiling",[0,2.71,z],[2.36,0.12,0.99],"warm_panel",True,"corridor")
    for x in (-1.20,1.20):
        box("corridor-wall",[x,1.30,z],[0.12,2.6,0.99],"panel",True,"corridor")
        box("corridor-rail",[x*0.92,0.94,z],[0.035,0.035,0.95],"metal",False,"corridor")
    box("corridor-light",[0,2.635,z],[0.48,0.015,0.09],"light",False,"lights")

# Compact common room: second furnished space, initially simpler than cabin.
box("common-floor",[0,-0.08,10.35],[5.0,0.17,5.0],"floor",True,"common")
box("common-ceiling",[0,2.78,10.35],[5.0,0.15,5.0],"warm_panel",True,"common")
for x in (-2.5,2.5):
    box("common-side",[x,1.35,10.35],[0.12,2.7,5.0],"panel",True,"common")
box("common-aft",[0,1.35,12.85],[5.0,2.7,0.12],"panel",True,"common")
for x in (-1.83,1.83):
    box("common-front",[x,1.35,7.90],[1.34,2.7,0.12],"panel",True,"common")
box("common-lamp",[0,2.69,10.35],[1.6,0.03,0.11],"light",False,"lights")
box("common-table",[0,0.77,10.30],[1.55,0.07,1.05],"warm_panel",True,"common")
box("common-table-leg",[0,0.37,10.30],[0.14,0.74,0.14],"metal",True,"common")
for z in (9.35,11.25):
    box("common-bench",[0,0.46,z],[1.8,0.15,0.48],"fabric",True,"common")
    for x in (-0.60,0.60):
        box("bench-leg",[x,0.20,z],[0.10,0.4,0.30],"metal",False,"common")
box("galley-counter",[-2.02,0.48,11.80],[0.75,0.96,1.45],"panel",True,"common")
box("galley-top",[-2.02,0.99,11.80],[0.78,0.06,1.48],"metal",False,"common")
box("galley-appliance",[-2.03,1.22,12.15],[0.51,0.42,0.42],"graphite",False,"common")

layout = dict(title="Orbital Habitat", version=1, units="metres",
    materials=materials, objects=items,
    spawn=[-0.55,0,-1.75], earth=dict(position=[0,-3000,-4200],radius=3500),
    roomBounds=[[-3.08,3.08,-3.67,3.7],[-1.10,1.10,3.65,8.0],[-2.36,2.36,7.9,12.68]])
(ROOT/'Assets'/'layout.json').write_text(json.dumps(layout,indent=2))
print(f"Created shared layout with {len(items)} objects")
