import bpy
import bmesh
import argparse
import sys
import mathutils

argv = sys.argv
if "--" not in argv:
    argv = []
else:
   argv = argv[argv.index("--") + 1:]

try:
    parser = argparse.ArgumentParser(description='Exports Blender model as a byte array for trifill rendering',prog = "blender -b -P "+__file__+" --")
    parser.add_argument('-o','--out', help='Output file', required=True, dest='out')
    args = parser.parse_args(argv)
except Exception as e:
    sys.exit(repr(e))

obdata = bpy.context.object.data
obj = bpy.context.object

# charset
charset="_0123456789abcdefghijklmnopqrstuvwxyz"

def pack_float(x):
    h = "{:02x}".format(int(round(32*x+128,0)))
    if len(h)!=2:
        raise Exception('Unable to convert: {} into a byte: {}'.format(x,h))
    return h

p8_colors = ['000000','1D2B53','7E2553','008751','AB5236','5F574F','C2C3C7','FFF1E8','FF004D','FFA300','FFEC27','00E436','29ADFF','83769C','FF77A8','FFCCAA']
def diffuse_to_p8color(rgb):
    h = "{:02X}{:02X}{:02X}".format(int(round(255*rgb.r)),int(round(255*rgb.g)),int(round(255*rgb.b)))
    try:
        #print("diffuse:{} -> {}\n".format(rgb,p8_colors.index(h)))
        return p8_colors.index(h)
    except Exception as e:
        # unknown color: purple!
        return 14

# model data
s = ""

# object name
name = bpy.context.object.name.lower()
s = s + "{:02x}".format(len(name))
for c in name:
    s = s + "{:02x}".format(charset.index(c)+1)

# scale (custom model property)
s = s + "{:02x}".format(bpy.context.object.get("scale", 1))

bm = bmesh.new()
bm.from_mesh(obdata)

s = s + "{:02x}".format(len(obdata.vertices))
for v in obdata.vertices:
    s = s + "{}{}{}".format(pack_float(v.co.x), pack_float(v.co.z), pack_float(v.co.y))

# faces:
s = s + "{:02x}".format(len(bm.faces))
for f in bm.faces:
    # vertex count
    s = s + "{:02x}".format(len(f.verts))
    # vertice id's
    for v in f.verts:
        s = s + "{:02x}".format(v.index+1)
    # center point
    v = f.calc_center_median_weighted()
    s = s + "{}{}{}".format(pack_float(v.x), pack_float(v.z), pack_float(v.y))
    # + color
    if obj.material_slots:
        slot = obj.material_slots[f.material_index]
        mat = slot.material
        s = s + "{:02x}".format(diffuse_to_p8color(mat.diffuse_color))
        # + dual-sided?
        s = s + "{:02x}".format(0 if mat.game_settings.use_backface_culling else 1)
    else:
        s = s + "{:02x}{:02x}".format(0,0)

#normals
s = s + "{:02x}".format(len(obdata.polygons))
for f in obdata.polygons:
    s = s + "{}{}{}".format(pack_float(f.normal.x), pack_float(f.normal.z), pack_float(f.normal.y))

#
with open(args.out, 'w') as f:
    f.write(s)

