import torch
from pathlib import Path
from torch.utils.data import DataLoader

from model_v4 import TrafficDetectorV4
from traffic_dataset_v4 import TrafficDatasetV4

# ==========================================================
# CONFIG
# ==========================================================
NUM_CLASSES = 15
IMAGE_SIZE = 448
MATCH_IOU = 0.50

# Focus around the calibrated ambulance operating point.
CONFIDENCE_THRESHOLDS = [0.95, 0.96, 0.97, 0.98]
NMS_THRESHOLDS = [0.40, 0.35, 0.30, 0.25, 0.20]

# None = ordinary NMS only.
# Otherwise suppress a lower-confidence same-class box when
# intersection / area(smaller box) >= threshold.
CONTAINMENT_THRESHOLDS = [None, 0.70, 0.80, 0.90]

BATCH_SIZE = 8
NUM_WORKERS = 4

MODEL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = MODEL_DIR.parent
MODEL_PATH = MODEL_DIR / "traffic_detector_v4_best.pth"

IMAGE_DIR = PROJECT_DIR / "ambulance_v4" / "valid" / "images"
LABEL_DIR = PROJECT_DIR / "ambulance_v4" / "valid" / "labels"


def collate(batch):
    return (
        torch.stack([x[0] for x in batch]),
        [x[1] for x in batch],
        [x[2] for x in batch],
        [x[3] for x in batch],
    )


def area(b):
    return max(0.0, b[2]-b[0]) * max(0.0, b[3]-b[1])


def intersection(a, b):
    x1=max(a[0],b[0]); y1=max(a[1],b[1])
    x2=min(a[2],b[2]); y2=min(a[3],b[3])
    return max(0.0,x2-x1)*max(0.0,y2-y1)


def iou(a, b):
    inter=intersection(a,b)
    union=area(a)+area(b)-inter
    return inter/union if union>0 else 0.0


def containment(a, b):
    """Intersection divided by area of the smaller box."""
    small=min(area(a),area(b))
    return intersection(a,b)/small if small>0 else 0.0


def postprocess(detections, nms_threshold, containment_threshold):
    detections=sorted(detections,key=lambda d:d["confidence"],reverse=True)
    kept=[]

    while detections:
        best=detections.pop(0)
        kept.append(best)
        remaining=[]

        for d in detections:
            # This sweep is ambulance-only, but keep class check explicit.
            if d["class_id"] != best["class_id"]:
                remaining.append(d)
                continue

            overlap=iou(best["box"],d["box"])
            contained=containment(best["box"],d["box"])

            suppress = overlap >= nms_threshold

            if (
                not suppress
                and containment_threshold is not None
                and contained >= containment_threshold
            ):
                suppress=True

            if not suppress:
                remaining.append(d)

        detections=remaining

    return kept


def decode_head(prediction, min_conf):
    obj=torch.sigmoid(prediction[0])
    probs=torch.softmax(prediction[5:],dim=0)
    class_prob,class_id=torch.max(probs,dim=0)
    conf=obj*class_prob

    rows,cols=torch.where(conf>=min_conf)
    if rows.numel()==0:
        return []

    tx=torch.sigmoid(prediction[1,rows,cols])
    ty=torch.sigmoid(prediction[2,rows,cols])
    w=torch.sigmoid(prediction[3,rows,cols])
    h=torch.sigmoid(prediction[4,rows,cols])

    gh,gw=prediction.shape[-2:]
    cx=(cols.float()+tx)/gw
    cy=(rows.float()+ty)/gh

    x1=torch.clamp(cx-w/2,0,1)
    y1=torch.clamp(cy-h/2,0,1)
    x2=torch.clamp(cx+w/2,0,1)
    y2=torch.clamp(cy+h/2,0,1)

    out=[]
    for k in range(rows.numel()):
        cid=int(class_id[rows[k],cols[k]])
        if cid != 14:
            continue

        box=(float(x1[k]),float(y1[k]),float(x2[k]),float(y2[k]))
        if box[2] <= box[0] or box[3] <= box[1]:
            continue

        out.append({
            "confidence":float(conf[rows[k],cols[k]]),
            "class_id":14,
            "box":box,
        })

    return out


def decode_raw_ambulance(outputs, batch_index, min_conf):
    small=outputs["small"][batch_index].detach().float().cpu()
    large=outputs["large"][batch_index].detach().float().cpu()
    return decode_head(small,min_conf)+decode_head(large,min_conf)


def build_gt(boxes, categories):
    out=[]
    for box,cat in zip(boxes,categories):
        if int(cat.item()) != 14:
            continue
        x,y,w,h=map(float,box.tolist())
        b=(
            max(0.0,min(1.0,x)),
            max(0.0,min(1.0,y)),
            max(0.0,min(1.0,x+w)),
            max(0.0,min(1.0,y+h)),
        )
        if b[2]>b[0] and b[3]>b[1]:
            out.append(b)
    return out


def match(predictions, gt):
    predictions=sorted(predictions,key=lambda d:d["confidence"],reverse=True)
    used=set()
    tp=0

    for p in predictions:
        best_iou=0.0
        best_idx=None

        for j,g in enumerate(gt):
            if j in used:
                continue
            v=iou(p["box"],g)
            if v>best_iou:
                best_iou=v
                best_idx=j

        if best_idx is not None and best_iou>=MATCH_IOU:
            tp+=1
            used.add(best_idx)

    fp=len(predictions)-tp
    fn=len(gt)-len(used)
    return tp,fp,fn


def load_model(device):
    model=TrafficDetectorV4(num_classes=NUM_CLASSES).to(device)
    loaded=torch.load(MODEL_PATH,map_location=device,weights_only=True)

    if isinstance(loaded,dict) and "model_state_dict" in loaded:
        state=loaded["model_state_dict"]
    elif isinstance(loaded,dict) and "model" in loaded and isinstance(loaded["model"],dict):
        state=loaded["model"]
    else:
        state=loaded

    model.load_state_dict(state)
    model.eval()
    return model


def main():
    for p in [MODEL_PATH,IMAGE_DIR,LABEL_DIR]:
        if not p.exists():
            raise FileNotFoundError(p)

    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset=TrafficDatasetV4(
        IMAGE_DIR,
        LABEL_DIR,
        image_size=IMAGE_SIZE,
        augment=False,
    )

    args=dict(
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=device.type=="cuda",
        collate_fn=collate,
    )
    if NUM_WORKERS>0:
        args.update(persistent_workers=True,prefetch_factor=2)

    loader=DataLoader(dataset,**args)
    model=load_model(device)

    min_conf=min(CONFIDENCE_THRESHOLDS)

    # Cache raw class-14 candidates once so all post-processing
    # configurations are compared on identical model outputs.
    cached=[]

    print("="*110)
    print("AMBULANCE NMS + CONTAINMENT SWEEP")
    print("="*110)
    print("Device:",device)
    print("Images:",len(dataset))
    print("Official match IoU:",MATCH_IOU)
    print("Minimum cached confidence:",min_conf)

    processed=0
    with torch.inference_mode():
        for images,boxes,categories,_ in loader:
            x=images.to(device,non_blocking=True)

            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=device.type=="cuda",
            ):
                outputs=model(x)

            for i in range(images.shape[0]):
                raw=decode_raw_ambulance(outputs,i,min_conf)
                gt=build_gt(boxes[i],categories[i])
                cached.append((raw,gt))
                processed+=1

            if processed%100 < images.shape[0]:
                print(f"Processed {processed}/{len(dataset)}")

    results=[]

    for conf in CONFIDENCE_THRESHOLDS:
        for nms_t in NMS_THRESHOLDS:
            for contain_t in CONTAINMENT_THRESHOLDS:
                TP=FP=FN=PRED=0

                for raw,gt in cached:
                    selected=[
                        d for d in raw
                        if d["confidence"]>=conf
                    ]

                    selected=postprocess(
                        selected,
                        nms_t,
                        contain_t,
                    )

                    tp,fp,fn=match(selected,gt)
                    TP+=tp; FP+=fp; FN+=fn; PRED+=len(selected)

                precision=TP/(TP+FP) if TP+FP else 0.0
                recall=TP/(TP+FN) if TP+FN else 0.0
                f1=(
                    2*precision*recall/(precision+recall)
                    if precision+recall else 0.0
                )

                results.append({
                    "conf":conf,
                    "nms":nms_t,
                    "contain":contain_t,
                    "pred":PRED,
                    "tp":TP,
                    "fp":FP,
                    "fn":FN,
                    "precision":precision,
                    "recall":recall,
                    "f1":f1,
                })

    results.sort(key=lambda r:r["f1"],reverse=True)

    print("\n"+"="*118)
    print("TOP 20 CONFIGURATIONS BY OFFICIAL F1")
    print("="*118)
    print(
        f"{'Rank':<6}{'Conf':<8}{'NMS':<8}{'Contain':<10}"
        f"{'Pred':<8}{'TP':<8}{'FP':<8}{'FN':<8}"
        f"{'Prec':<10}{'Recall':<10}{'F1':<10}"
    )
    print("-"*118)

    for rank,r in enumerate(results[:20],1):
        contain="OFF" if r["contain"] is None else f"{r['contain']:.2f}"
        print(
            f"{rank:<6}{r['conf']:<8.2f}{r['nms']:<8.2f}{contain:<10}"
            f"{r['pred']:<8}{r['tp']:<8}{r['fp']:<8}{r['fn']:<8}"
            f"{r['precision']:<10.4f}{r['recall']:<10.4f}{r['f1']:<10.4f}"
        )

    best=results[0]
    contain="OFF" if best["contain"] is None else f"{best['contain']:.2f}"

    print("\nBEST CONFIGURATION")
    print("-"*50)
    print(f"Confidence : {best['conf']:.2f}")
    print(f"NMS IoU    : {best['nms']:.2f}")
    print(f"Containment: {contain}")
    print(f"TP         : {best['tp']}")
    print(f"FP         : {best['fp']}")
    print(f"FN         : {best['fn']}")
    print(f"Precision  : {best['precision']:.4f}")
    print(f"Recall     : {best['recall']:.4f}")
    print(f"F1         : {best['f1']:.4f}")
    print("="*118)


if __name__=="__main__":
    main()
