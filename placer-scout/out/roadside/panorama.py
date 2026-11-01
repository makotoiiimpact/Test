import rasterio, numpy as np, json
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from PIL import Image, ImageDraw
from pyproj import Transformer
m=json.load(open("s2m.json")); img=np.array(Image.open("s2m.png")); H,W=img.shape[:2]
tr=from_origin(m["x0"],m["y1"],10,10)
dem=np.zeros((H,W),np.float32)
with rasterio.open("dem.tif") as ds:
    reproject(ds.read(1),dem,src_transform=ds.transform,src_crs=ds.crs,dst_transform=tr,dst_crs="EPSG:32611",resampling=Resampling.bilinear)
t=Transformer.from_crs(4326,32611,always_xy=True)
vx,vy=t.transform(-116.2348,35.1187); c0,r0=(vx-m["x0"])/10,(m["y1"]-vy)/10
eye=dem[int(r0),int(c0)]+2; print("eye elev",eye)
az=np.arange(250,400,0.05)%360; nA=len(az)
dist=np.arange(50,22000,10.0)
el_px=0.05  # deg per row
rows=int(14/el_px); pano=np.full((rows,nA,3),[200,210,225],np.uint8); hit=np.zeros((rows,nA,2),np.float32)
R=6371000.0
for j,a in enumerate(az):
    dx,dy=np.sin(np.radians(a)),np.cos(np.radians(a))
    cc=c0+dx*dist/10; rr=r0-dy*dist/10
    ok=(cc>=0)&(cc<W-1)&(rr>=0)&(rr<H-1)
    ci,ri=cc[ok].astype(int),rr[ok].astype(int); d=dist[ok]
    z=dem[ri,ci]-d**2/(2*R)*0.87
    ang=np.degrees(np.arctan2(z-eye,d))
    top=-np.inf
    for k in range(len(d)):
        if ang[k]>top:
            lo=top if np.isfinite(top) else ang[k]-0.5
            r_lo=int((10-ang[k])/el_px); r_hi=int((10-max(lo,-4))/el_px)
            r_lo=max(r_lo,0); r_hi=min(r_hi,rows)
            if r_hi>r_lo:
                pano[r_lo:r_hi,j]=img[ri[k],ci[k]]; hit[r_lo:r_hi,j]=(ci[k],ri[k])
            top=ang[k]
Image.fromarray(pano).save("pano.png"); np.save("hit.npy",hit)
p=Image.fromarray(pano); d=ImageDraw.Draw(p)
for j in range(0,nA,200): d.text((j,rows-12),str(int(az[j])),fill=(255,0,0)); d.line([(j,rows-20),(j,rows)],fill=(255,0,0))
p.save("pano_lab.png"); print(p.size)
