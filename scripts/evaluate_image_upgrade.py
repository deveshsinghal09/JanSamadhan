"""Compare checkpoints on the new outdoor-litter holdout, before promotion."""
import csv,json
from collections import Counter
from pathlib import Path
import torch
from torch.utils.data import DataLoader
from ml.train_images import Images
from ml.vision import architecture

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'data/image-v2-run'
def main():
 torch.set_num_threads(4)
 with (RUN/'data/images/manifest.csv').open() as f:rows=[r for r in csv.DictReader(f) if r['split']=='test' and '/taco/' in r['path']]
 result={'images':len(rows),'batches':len({r['source_family'] for r in rows}),'note':'Same held-out TACO acquisition batches for both models; these images were absent from v1 training and v2 training/validation. Recall measures litter recognition only, not false positives on non-litter images. Old and new overall test sets differ, so overall accuracy is not a paired comparison.'}
 for version,path in [('v1',ROOT/'data/images/archive/image-v1/image_model.pt'),('v2',RUN/'ml/image_model.pt')]:
  ck=torch.load(path,map_location='cpu',weights_only=True);labels=ck['labels'];net=architecture(len(labels));net.load_state_dict(ck['state_dict']);net.eval()
  # Dataset targets are unused here; retain the current row labels for loading.
  loader=DataLoader(Images(rows,['Garbage / litter']),batch_size=32)
  predictions=[]
  with torch.inference_mode():
   for x,_ in loader:predictions.extend(labels[i] for i in net(x).argmax(1).tolist())
  result[version+'_recall']=sum(label in ('Waste material','Garbage / litter') for label in predictions)/len(rows)
  result[version+'_predictions']=dict(Counter(predictions))
 metrics_path=RUN/'data/image_metrics.json';metrics=json.loads(metrics_path.read_text());metrics['outdoor_litter_evaluation']=result;metrics_path.write_text(json.dumps(metrics,indent=2))
 (RUN/'data/images/outdoor_litter_comparison.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
