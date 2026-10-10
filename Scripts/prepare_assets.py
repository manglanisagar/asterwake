"""Prepare bounded-size textures and unpack the sample character's embedded maps."""
from pathlib import Path
import json, struct, random
from PIL import Image, ImageDraw, ImageFilter

root = Path(__file__).resolve().parent.parent
out = root/'Assets'/'Textures'
out.mkdir(exist_ok=True)
for name, width in [('earth-day',8192),('earth-night',4096),('earth-clouds',4096),('stars-milky-way',4096)]:
    im = Image.open(root/'Assets'/'Source'/f'{name}.jpg').convert('RGB')
    if im.width > width: im = im.resize((width,width*im.height//im.width),Image.Resampling.LANCZOS)
    im.save(out/f'{name}.jpg',quality=92)

# A texture-format conversion: cloud luminance is the opacity channel. SceneKit
# can read standard PNG alpha directly, avoiding ambiguous RGB opacity modes.
cloud=Image.open(out/'earth-clouds.jpg').convert('L')
cloud=cloud.point(lambda v: max(0,min(210,int((v-45)*1.4))))
rgba=Image.new('RGBA',cloud.size,(245,250,255,255));rgba.putalpha(cloud)
rgba.save(out/'earth-clouds-alpha.png')

rng=random.Random(42)
for name,base in [('panel',(175,179,171)),('floor',(57,64,69)),('fabric',(56,68,76))]:
    im=Image.new('RGB',(512,512)); pix=im.load()
    for y in range(512):
        for x in range(512):
            noise=rng.randint(-3,3)
            weave=(-4 if x%4==0 else 0)+(-3 if y%4==0 else 0) if name=='fabric' else 0
            pix[x,y]=tuple(max(0,min(255,c+noise+weave)) for c in base)
    d=ImageDraw.Draw(im)
    if name=='floor':
        for y in range(12,512,28):
            for x in range(12,512,28):
                d.line((x-5,y+4,x+5,y-4),fill=(78,86,91),width=2)
        d.rectangle((1,1,510,510),outline=(34,41,45),width=3)
    elif name=='panel':
        for i in range(45):
            x,y=rng.randrange(512),rng.randrange(512)
            d.line((x,y,min(511,x+rng.randrange(3,22)),y+1),fill=(152,158,152),width=1)
    im.save(out/f'{name}-detail.jpg',quality=94)

glb=(root/'Assets'/'Source'/'Crew.glb').read_bytes()
jlen=struct.unpack_from('<I',glb,12)[0]; data=json.loads(glb[20:20+jlen])
bstart=20+jlen+8; binary=glb[bstart:]
for i,im in enumerate(data.get('images',[])):
    view=data['bufferViews'][im['bufferView']]
    ext='png' if im.get('mimeType')=='image/png' else 'jpg'
    (out/f'character-{i}.{ext}').write_bytes(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])
print('Textures prepared, character maps unpacked')
