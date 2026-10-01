"""Train a pothole detector and evaluate the selected checkpoint without deployment."""
import json,hashlib,os,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('YOLO_CONFIG_DIR',str(ROOT/'.training-tmp/yolo'))
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--resume",type=Path);args=parser.parse_args()
 from ultralytics import YOLO,settings
 settings.update({'sync':False,'wandb':False,'mlflow':False,'clearml':False,'comet':False})
 import ultralytics
 data=ROOT/'data/images/pothole-detector-rdd/dataset.yaml'
 if not data.exists():raise SystemExit('Run scripts/build_pothole_detector_layout.py first')
 # Standard COCO initialization, never the supplied pothole photograph.
 if args.resume:
  model=YOLO(str(args.resume));model.train(resume=True)
 else:
  model=YOLO('yolov8n.pt')
  model.train(data=str(data),epochs=40,patience=7,imgsz=640,batch=4,workers=0,device=0,seed=42,deterministic=True,project=str(ROOT/'data/pothole-detector-runs'),name='rdd-v1',exist_ok=False,cache=False,close_mosaic=10,amp=False)
 run=Path(model.trainer.save_dir);best=YOLO(str(run/'weights/best.pt'))
 metrics=best.val(data=str(data),split='test',imgsz=640,batch=4,workers=0,device=0,project=str(run),name='heldout-test')
 external=best.predict(source=str(ROOT/'tests/fixtures/external-pothole.jpg'),imgsz=640,conf=.25,device=0,save=True,project=str(run),name='external-diagnostic')[0]
 report={'ultralytics_version':ultralytics.__version__,'checkpoint_sha256':hashlib.sha256((run/'weights/best.pt').read_bytes()).hexdigest(),'test_metrics':{k:float(v) for k,v in metrics.results_dict.items()},'external_boxes':external.boxes.xyxy.cpu().tolist(),'external_scores':external.boxes.conf.cpu().tolist(),'policy':'COCO-pretrained YOLOv8n fine-tuned on RDD India D40 boxes. Existing sequence groups retained. Test split evaluated after validation-selected checkpoint. External photo excluded from project training; no automatic deployment. Detection scores and mAP are not classification accuracy. Non-road false-positive challenge evaluation still required.'}
 (run/'evaluation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
