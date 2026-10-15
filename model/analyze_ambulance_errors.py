# V4 ambulance error visualization
import json
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader
from model_v4 import TrafficDetectorV4
from traffic_dataset_v4 import TrafficDatasetV4

NUM_CLASSES=15
IMAGE_SIZE=448
CONF=0.97
NMS_IOU=0.40
MATCH_IOU=0.50
BATCH_SIZE=8
NUM_WORKERS=4
MODEL_DIR=Path(__file__).resolve().parent
PROJECT_DIR=MODEL_DIR.parent
MODEL_PATH=MODEL_DIR/"traffic_detector_v4_best.pth"
IMAGE_DIR=PROJECT_DIR/"ambulance_v4"/"valid"/"images"
LABEL_DIR=PROJECT_DIR/"ambulance_v4"/"valid"/"labels"
OUT=PROJECT_DIR/"ambulance_error_analysis_v4"
MAX_SAVE=100

def collate(batch):
    return torch.stack([x[0] for x in batch]),[x[1] for x in batch],[x[2] for x in batch],[x[3] for x in batch]

def iou(a,b):
    x1,y1=max(a[0],b[0]),max(a[1],b[1]); x2,y2=min(a[2],b[2]),min(a[3],b[3])
    inter=max(0,x2-x1)*max(0,y2-y1)
    aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]); ab=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    u=aa+ab-inter
    return inter/u if u>0 else 0.0

def nms(ds):
    ds=sorted(ds,key=lambda d:d["confidence"],reverse=True); kept=[]
    while ds:
        best=ds.pop(0); kept.append(best)
        ds=[d for d in ds if d["class_id"]!=best["class_id"] or iou(best["box"],d["box"])<NMS_IOU]
    return kept

def decode_head(p):
    obj=torch.sigmoid(p[0]); probs=torch.softmax(p[5:],dim=0)
    cp,cid=torch.max(probs,dim=0); conf=obj*cp
    rows,cols=torch.where(conf>=CONF)
    if rows.numel()==0:return []
    tx=torch.sigmoid(p[1,rows,cols]); ty=torch.sigmoid(p[2,rows,cols])
    w=torch.sigmoid(p[3,rows,cols]); h=torch.sigmoid(p[4,rows,cols])
    cx=(cols.float()+tx)/p.shape[2]; cy=(rows.float()+ty)/p.shape[1]
    x1=torch.clamp(cx-w/2,0,1); y1=torch.clamp(cy-h/2,0,1)
    x2=torch.clamp(cx+w/2,0,1); y2=torch.clamp(cy+h/2,0,1)
    out=[]
    for k in range(rows.numel()):
        box=(float(x1[k]),float(y1[k]),float(x2[k]),float(y2[k]))
        if box[2]>box[0] and box[3]>box[1]:
            out.append({"confidence":float(conf[rows[k],cols[k]]),"class_id":int(cid[rows[k],cols[k]]),"box":box})
    return out

def decode(outputs,i):
    ds=decode_head(outputs["small"][i].detach().float().cpu())+decode_head(outputs["large"][i].detach().float().cpu())
    return [d for d in nms(ds) if d["class_id"]==14]

def gt_boxes(boxes,cats):
    out=[]
    for b,c in zip(boxes,cats):
        if int(c)!=14:continue
        x,y,w,h=map(float,b.tolist())
        out.append({"box":(max(0,x),max(0,y),min(1,x+w),min(1,y+h))})
    return out

def match(pred,gt):
    used=set(); tp=[]; fp=[]
    for d in sorted(pred,key=lambda z:z["confidence"],reverse=True):
        best=-1; bi=0.0
        for j,g in enumerate(gt):
            if j in used:continue
            v=iou(d["box"],g["box"])
            if v>bi:bi=v;best=j
        q=dict(d)
        if best>=0 and bi>=MATCH_IOU:
            used.add(best);q["iou"]=bi;tp.append(q)
        else:q["iou"]=bi;fp.append(q)
    fn=[g for j,g in enumerate(gt) if j not in used]
    return tp,fp,fn

def to_img(t):
    a=np.clip(t.permute(1,2,0).numpy()*255,0,255).astype(np.uint8)
    return Image.fromarray(a)

def px(b):
    return tuple(int(v*IMAGE_SIZE) for v in b)

def draw(t,gt,tp,fp,fn):
    im=to_img(t); d=ImageDraw.Draw(im)
    for g in gt:d.rectangle(px(g["box"]),outline="blue",width=2)
    for z in tp:
        b=px(z["box"]);d.rectangle(b,outline="green",width=4);d.text((b[0],max(0,b[1]-12)),f"TP {z['confidence']:.3f}",fill="green")
    for z in fp:
        b=px(z["box"]);d.rectangle(b,outline="red",width=4);d.text((b[0],max(0,b[1]-12)),f"FP {z['confidence']:.3f}",fill="red")
    for g in fn:
        b=px(g["box"]);d.rectangle(b,outline="orange",width=4);d.text((b[0],b[3]),"FN",fill="orange")
    return im

def load_model(device):
    m=TrafficDetectorV4(num_classes=NUM_CLASSES).to(device)
    x=torch.load(MODEL_PATH,map_location=device,weights_only=True)
    if isinstance(x,dict) and "model_state_dict" in x:x=x["model_state_dict"]
    elif isinstance(x,dict) and "model" in x and isinstance(x["model"],dict):x=x["model"]
    m.load_state_dict(x);m.eval();return m

def main():
    for p in [MODEL_PATH,IMAGE_DIR,LABEL_DIR]:
        if not p.exists():raise FileNotFoundError(p)
    dirs={k:OUT/k for k in ["tp","fp","fn","mixed"]}
    for p in dirs.values():p.mkdir(parents=True,exist_ok=True)
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ds=TrafficDatasetV4(IMAGE_DIR,LABEL_DIR,image_size=IMAGE_SIZE,augment=False)
    args=dict(batch_size=BATCH_SIZE,shuffle=False,num_workers=NUM_WORKERS,pin_memory=device.type=="cuda",collate_fn=collate)
    if NUM_WORKERS>0:args.update(persistent_workers=True,prefetch_factor=2)
    loader=DataLoader(ds,**args);model=load_model(device)
    totals={"tp":0,"fp":0,"fn":0};saved={k:0 for k in dirs};records=[];idx=0
    print(f"Analyzing {len(ds)} images at confidence {CONF:.2f} on {device}")
    with torch.inference_mode():
        for images,boxes,cats,_ in loader:
            x=images.to(device,non_blocking=True)
            with torch.amp.autocast(device_type=device.type,dtype=torch.float16,enabled=device.type=="cuda"):
                outputs=model(x)
            for i in range(len(images)):
                pred=decode(outputs,i);gt=gt_boxes(boxes[i],cats[i]);tp,fp,fn=match(pred,gt)
                for k,v in [("tp",tp),("fp",fp),("fn",fn)]:totals[k]+=len(v)
                name=ds.image_files[idx].stem
                category=None
                if fp and not tp:category="fp"
                elif fn and not tp and not fp:category="fn"
                elif tp and not fp and not fn:category="tp"
                elif tp or fp or fn:category="mixed"
                if category and saved[category]<MAX_SAVE:
                    draw(images[i],gt,tp,fp,fn).save(dirs[category]/f"{name}_{category.upper()}.png");saved[category]+=1
                records.append({"image":ds.image_files[idx].name,"tp":len(tp),"fp":len(fp),"fn":len(fn)})
                idx+=1
                if idx%100==0:print(f"Processed {idx}/{len(ds)}")
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"summary.json").write_text(json.dumps({"threshold":CONF,"totals":totals,"saved":saved},indent=2))
    (OUT/"per_image_errors.json").write_text(json.dumps(records,indent=2))
    print("\nDONE",totals)
    print("Open:",OUT)
    print("Inspect first:",dirs["fp"])

if __name__=="__main__":
    main()
