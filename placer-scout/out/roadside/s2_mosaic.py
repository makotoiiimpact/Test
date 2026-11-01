import requests, rasterio, numpy as np, json
from rasterio.vrt import WarpedVRT
from rasterio.transform import from_origin
from PIL import Image, ImageDraw
from pyproj import Transformer
t=Transformer.from_crs(4326,32611,always_xy=True)
x0,y1=t.transform(-116.36,35.24); x1,y0=t.transform(-116.15,35.04)
W,H=int((x1-x0)/10),int((y1-y0)/10); tr=from_origin(x0,y1,10,10)
ids=["S2B_11SNU_20261019_0_L2A","S2B_11SNV_20261019_0_L2A"]
out=np.zeros((H,W,3))
for i in ids:
    f=requests.get(f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{i}",timeout=60).json()
    for k,b in enumerate(["red","green","blue"]):
        with rasterio.open(f["assets"][b]["href"]) as ds, WarpedVRT(ds,crs="EPSG:32611",transform=tr,width=W,height=H) as v:
            a=v.read(1).astype(float); m=(out[:,:,k]==0)&(a>0); out[:,:,k][m]=a[m]
lo,hi=np.percentile(out[out>0],1),np.percentile(out[out>0],99.5)
img=(np.clip((out-lo)/(hi-lo),0,1)**0.8*255).astype(np.uint8)
Image.fromarray(img).save("s2m.png")
json.dump({"x0":x0,"y1":y1},open("s2m.json","w"))
vx,vy=t.transform(-116.2348,35.1187); col,row=(vx-x0)/10,(y1-vy)/10
im=Image.fromarray(img); dr=ImageDraw.Draw(im)
dr.ellipse([col-15,row-15,col+15,row+15],outline=(255,0,0),width=5)
for i in range(0,W,200): dr.text((i,2),str(i),fill=(255,255,0))
for j in range(0,H,200): dr.text((2,j),str(j),fill=(255,255,0))
im.resize((W//2,H//2)).save("s2m_small.png"); print(W,H,col,row)
