#!/usr/bin/env python3
# scripts/gen_rom.py

import os
import sys
import numpy as np
from PIL import Image
from moviepy.editor import VideoFileClip

NES_PALETTE = np.array([
    [124,124,124],[0,0,252],[0,0,188],[68,40,188],
    # …（省略）…
    [0,0,0]
])

def map_to_tiles(frame, mode='color'):
    h,w,_ = frame.shape
    data=[]
    for ty in range(0,h,8):
        for tx in range(0,w,8):
            p0,p1=[],[]
            tile = frame[ty:ty+8,tx:tx+8]
            for row in tile:
                b0=b1=0
                for px in row:
                    r,g,b = px
                    if mode=='mono':
                        lum = 0.3*r + 0.59*g + 0.11*b
                        idx = 0 if lum>128 else 1
                    else:
                        d = ((NES_PALETTE-px)**2).sum(axis=1)
                        idx = int(np.argmin(d)) % 4
                    b0 = (b0<<1) | (idx&1)
                    b1 = (b1<<1) | ((idx>>1)&1)
                p0.append(b0); p1.append(b1)
            data += p0 + p1
    return data

def write_rom(data, out_path):
    prg_banks = 1
    chr_banks = (len(data)+8191)//8192
    header = bytearray(16)
    header[0:4] = b'NES\x1A'
    header[4] = prg_banks
    header[5] = chr_banks
    prg = bytearray(prg_banks*16384)
    chr_blob = bytearray(chr_banks*8192)
    chr_blob[:len(data)] = bytearray(data)
    with open(out_path,'wb') as f:
        f.write(header)
        f.write(prg)
        f.write(chr_blob)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv)>1 else 'color'
    os.makedirs('output', exist_ok=True)
    for fn in os.listdir('media'):
        if not fn.lower().endswith(('.png','.jpg','.jpeg','.mp4')):
            continue
        path = os.path.join('media', fn)
        if fn.lower().endswith(('.png','.jpg','.jpeg')):
            img = np.array(Image.open(path).convert('RGB').resize((256,240)))
            data = map_to_tiles(img, mode)
        else:
            clip = VideoFileClip(path)
            data = []
            for t in np.arange(0, clip.duration, 1/10):
                frame = clip.get_frame(t)
                arr = np.array(Image.fromarray(frame).resize((256,240)))
                data += map_to_tiles(arr, mode)
        write_rom(data, f'output/{os.path.splitext(fn)[0]}.nes')
        print(f"Generated output/{os.path.splitext(fn)[0]}.nes")
