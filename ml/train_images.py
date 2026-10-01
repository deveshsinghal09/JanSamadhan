"""Image classifier training with source-family/perceptual grouping before splitting.
python -m ml.train_images --epochs 8
"""
import argparse,csv,hashlib,json,os,random,re,time,zipfile
from collections import Counter,defaultdict
from pathlib import Path
os.environ.setdefault('TORCH_HOME',str(Path(__file__).resolve().parents[1]/'data/images/torch-cache'))
import numpy as np
import torch
from PIL import Image,ImageOps
from torch.utils.data import DataLoader,Dataset
from sklearn.metrics import classification_report,confusion_matrix,f1_score
from sklearn.model_selection import train_test_split
from ml.vision import ROOT,architecture,transform

BASE=ROOT/'data/images';RAW=BASE/'raw';SEED=42
SOURCE='https://www.kaggle.com/datasets/programmerrdai/road-issues-detection-dataset'
def image_label(path):
 name=str(path).lower()
 if 'dataset-resized' in name or '/taco/' in path.as_posix():return 'Garbage / litter'
 if 'mixed' in name:return None
 if 'littering' in name or 'garbage' in name:return 'Street scene / review'
 if 'vandalism' in name:return 'Graffiti'
 if 'pothole' in name:return 'Pothole'
 if 'damaged road issues' in name:return 'Road surface issue'
 if 'broken road sign' in name:return 'Damaged road sign'
 if 'illegal parking' in name:return 'Parking scene'
 return None
def dhash(image):
 a=np.asarray(image.convert('L').resize((9,8)),dtype=np.int16)
 return int.from_bytes(np.packbits(a[:,1:]>a[:,:-1]).tobytes(),'big')
class HashTree:
 def __init__(self):self.root=None
 def insert(self,value,index):
  if self.root is None:self.root=[value,index,{}];return
  node=self.root
  while True:
   d=(value^node[0]).bit_count()
   if not d:return
   if d not in node[2]:node[2][d]=[value,index,{}];return
   node=node[2][d]
 def neighbors(self,value,radius=4):
  stack=[self.root] if self.root else [];found=[]
  while stack:
   v,index,children=stack.pop();d=(value^v).bit_count()
   if d<=radius:found.append(index)
   stack.extend(child for dist,child in children.items() if d-radius<=dist<=d+radius)
  return found
def prepare(artifact_dir=BASE):
 artifact_dir.mkdir(parents=True,exist_ok=True)
 RAW.mkdir(parents=True,exist_ok=True)
 if not any(RAW.rglob('*.jpg')):
  with zipfile.ZipFile(BASE/'road-issues.zip') as z:
   for entry in z.infolist():
    destination=(RAW/entry.filename).resolve()
    if not destination.is_relative_to(RAW.resolve()):raise ValueError('Unsafe archive member')
   z.extractall(RAW)
 if not (RAW/'dataset-resized').exists():
  with zipfile.ZipFile(BASE/'trashnet.zip') as z:
   for entry in z.infolist():
    if not (RAW/entry.filename).resolve().is_relative_to(RAW.resolve()):raise ValueError('Unsafe archive member')
   z.extractall(RAW)
 records=[];rejected=Counter();pixel_seen=set()
 taco_metadata=json.loads((BASE/'taco_annotations.json').read_text()) if (BASE/'taco_annotations.json').exists() else {'images':[]}
 taco_batches={f"taco_{im['id']:05}":im['file_name'].split('/')[0] for im in taco_metadata['images']}
 paths=sorted(p for p in RAW.rglob('*') if p.suffix.lower() in ('.jpg','.jpeg','.png') and '__MACOSX' not in p.parts and not p.name.startswith('._'))
 for p in paths:
  label=image_label(p)
  if not label:rejected['unsupported_or_mixed']+=1;continue
  try:
   with Image.open(p) as im:
    im=ImageOps.exif_transpose(im).convert('RGB');im.load()
    if min(im.size)<32:rejected['too_small']+=1;continue
    small=np.asarray(im.resize((64,64)))
    if np.mean(np.max(small,axis=2)<8)>.18:rejected['heavily_black_or_occluded']+=1;continue
    pixel_hash=hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
    visual_hash=dhash(im)
   # Keep duplicate labels until group conflict detection; discard only same-label duplicates.
   if (pixel_hash,label) in pixel_seen:rejected['exact_duplicate_same_label']+=1;continue
   pixel_seen.add((pixel_hash,label))
   family=re.split(r'\.rf\.|_rf_',p.stem)[0]
   family=re.sub(r'(_jpg|_jpeg|_png)$','',family)
   family=re.sub(r'_A\d+$','',family)
   if p.parent.name=='taco':family='TACO-'+taco_batches[p.stem]
   records.append({'path':p.relative_to(ROOT).as_posix(),'label':label,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixel_hash':pixel_hash,'dhash':str(visual_hash),'source_family':family})
  except (OSError,ValueError):rejected['decode_failed']+=1
 parent=list(range(len(records)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 families={};pixels={};tree=HashTree()
 for i,r in enumerate(records):
  for registry,key in [(families,r['source_family']),(pixels,r['pixel_hash'])]:
   if key in registry:parent[find(i)]=find(registry[key])
   else:registry[key]=i
  value=int(r['dhash'])
  for neighbor in tree.neighbors(value):parent[find(i)]=find(neighbor)
  tree.insert(value,i)
 groups=defaultdict(list)
 for i,r in enumerate(records):groups[find(i)].append(r)
 valid=[]
 for g in groups.values():
  if len({r['label'] for r in g})>1:rejected['conflicting_group_images']+=len(g)
  else:valid.append(g)
 ids=list(range(len(valid)));strata=[g[0]['label']+(':TACO' if any('/taco/' in r['path'] for r in g) else ':original') for g in valid]
 train,hold=train_test_split(ids,test_size=.30,stratify=strata,random_state=SEED)
 val,test=train_test_split(hold,test_size=.5,stratify=[strata[i] for i in hold],random_state=SEED)
 assignment={i:s for s,subset in [('train',train),('validation',val),('test',test)] for i in subset}
 rows=[]
 for i,g in enumerate(valid):
  for r in g:rows.append(r|{'group':f'IMG-GROUP-{i:05}','split':assignment[i]})
 with (artifact_dir/'manifest.csv').open('w',newline='',encoding='utf8') as f:
  writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
 audit={'downloaded_image_files':len(paths),'retained_images':len(rows),'groups':len(valid),'rejected':dict(rejected),'class_counts':{s:dict(Counter(r['label'] for r in rows if r['split']==s)) for s in ['train','validation','test']},'split_policy':'Group by source filename before .rf augmentation suffix, exact decoded pixels and 64-bit difference-hash Hamming distance <=4. Remove conflicting-label groups. TACO photographs additionally grouped by acquisition batch, stratified separately from original sources. Stratified group 70/15/15, seed 42. Near duplicates outside these heuristics may remain.'}
 (artifact_dir/'audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2),flush=True)
 return rows,audit
class Images(Dataset):
 def __init__(self,rows,labels,training=False,size=224,preserve_frame=False):self.rows=rows;self.labels=labels;self.preprocess=transform(training,size,preserve_frame)
 def __len__(self):return len(self.rows)
 def __getitem__(self,i):
  row=self.rows[i]
  cache=ROOT/'.training-tmp/image-cache'/f"{row['sha256']}.png"
  if cache.exists():
   with Image.open(cache) as im:image=im.convert('RGB')
  else:
   with Image.open(ROOT/row['path']) as im:image=ImageOps.exif_transpose(im).convert('RGB')
   image.thumbnail((768,768));cache.parent.mkdir(parents=True,exist_ok=True);image.save(cache)
  return self.preprocess(image),self.labels.index(row['label'])
def evaluate(model,loader,device,labels):
 truth=[];pred=[];prob=[]
 model.eval()
 with torch.inference_mode():
  for x,y in loader:
   p=torch.softmax(model(x.to(device)),1).cpu();truth.extend(y.tolist());pred.extend(p.argmax(1).tolist());prob.extend(p.tolist())
 return {'report':classification_report(truth,pred,labels=list(range(len(labels))),target_names=labels,output_dict=True,zero_division=0),'labels':labels,'confusion_matrix':confusion_matrix(truth,pred,labels=list(range(len(labels)))).tolist()},np.asarray(truth),np.asarray(prob)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--epochs',type=int,default=8);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--run-dir',type=Path,default=ROOT);parser.add_argument('--version',default='image-v2');parser.add_argument('--manifest',type=Path)
 parser.add_argument('--architecture',choices=['mobilenet_v3_small','mobilenet_v3_large'],default='mobilenet_v3_small');parser.add_argument('--image-size',type=int,default=224);parser.add_argument('--batch-size',type=int,default=32);parser.add_argument('--preserve-frame',action='store_true');parser.add_argument('--init-checkpoint',type=Path);args=parser.parse_args()
 run=args.run_dir.resolve();artifact_dir=run/'data/images';model_path=run/'ml/image_model.pt'
 model_path.parent.mkdir(parents=True,exist_ok=True)
 random.seed(SEED);np.random.seed(SEED);torch.manual_seed(SEED);torch.set_num_threads(4)
 if args.manifest:
  import shutil
  source_manifest=args.manifest.resolve();artifact_dir.mkdir(parents=True,exist_ok=True)
  with source_manifest.open(encoding='utf8') as f:rows=list(csv.DictReader(f))
  audit=json.loads(source_manifest.with_name('audit.json').read_text())
  if source_manifest!=artifact_dir/'manifest.csv':
   shutil.copy2(source_manifest,artifact_dir/'manifest.csv');shutil.copy2(source_manifest.with_name('audit.json'),artifact_dir/'audit.json')
 else:rows,audit=prepare(artifact_dir)
 if args.prepare_only:return
 started=time.time();labels=sorted({r['label'] for r in rows});device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
 print('DEVICE',device,'CLASSES',labels,flush=True)
 loaders={s:DataLoader(Images([r for r in rows if r['split']==s],labels,s=='train',args.image_size,args.preserve_frame),batch_size=args.batch_size,shuffle=s=='train',num_workers=0) for s in ['train','validation','test']}
 model=architecture(len(labels),pretrained=True,name=args.architecture).to(device)
 if args.init_checkpoint:
  initial=torch.load(args.init_checkpoint,map_location='cpu',weights_only=True)
  if initial['labels']!=labels or initial.get('architecture','mobilenet_v3_small')!=args.architecture:raise ValueError('Initialization checkpoint labels or architecture differ')
  model.load_state_dict(initial['state_dict']);del initial
  print('Initialized from saved candidate; optimizer and epoch counter restart',flush=True)
 for p in model.features.parameters():p.requires_grad=False
 counts=Counter(r['label'] for r in rows if r['split']=='train');weights=torch.tensor([len(loaders['train'].dataset)/(len(labels)*counts[l]) for l in labels],device=device)
 criterion=torch.nn.CrossEntropyLoss(weight=weights)
 optimizer=torch.optim.AdamW(model.classifier.parameters(),lr=.001,weight_decay=.01)
 history=[];best=-1.;best_epoch=0;stale=0
 for epoch in range(args.epochs):
  if epoch==2:
   for p in model.features.parameters():p.requires_grad=True
   optimizer=torch.optim.AdamW([{'params':model.features.parameters(),'lr':.00005},{'params':model.classifier.parameters(),'lr':.0003}],weight_decay=.01)
  model.train()
  if epoch<2:model.features.eval()
  # Keep pretrained running statistics stable; weights still learn during fine-tuning.
  for module in model.modules():
   if isinstance(module,torch.nn.BatchNorm2d):module.eval()
  total_loss=0;seen=0
  for x,y in loaders['train']:
   x=x.to(device);y=y.to(device);optimizer.zero_grad(set_to_none=True)
   output=model(x);loss=criterion(output,y);loss.backward();optimizer.step();total_loss+=loss.item()*len(y);seen+=len(y)
  report,_,_=evaluate(model,loaders['validation'],device,labels);f1=report['report']['macro avg']['f1-score']
  record={'epoch':epoch+1,'stage':'classifier warm-up' if epoch<2 else 'full CNN fine-tuning','train_loss':total_loss/seen,'validation_macro_f1':f1,'validation_accuracy':report['report']['accuracy']};history.append(record);print(json.dumps(record),flush=True)
  if f1>best:
   best=f1;best_epoch=epoch+1;stale=0
   torch.save({'state_dict':{k:v.detach().cpu() for k,v in model.state_dict().items()},'labels':labels,'version':args.version,'review_threshold':.70,'architecture':args.architecture,'image_size':args.image_size,'max_edge':768},model_path)
  else:stale+=1
  (artifact_dir/'training_history.json').write_text(json.dumps(history,indent=2))
  if stale>=3 and epoch>=4:break
 checkpoint=torch.load(model_path,map_location=device,weights_only=True);model.load_state_dict(checkpoint['state_dict'])
 val,val_truth,val_prob=evaluate(model,loaders['validation'],device,labels)
 from scipy.optimize import minimize_scalar
 from scipy.special import softmax
 val_logits=np.log(np.clip(val_prob,1e-12,1))
 objective=lambda temperature:float(-np.log(np.clip(softmax(val_logits/temperature,axis=1)[np.arange(len(val_truth)),val_truth],1e-12,1)).mean())
 temperature=float(minimize_scalar(objective,bounds=(.5,5.),method='bounded').x)
 calibrated=softmax(val_logits/temperature,axis=1)
 thresholds={};threshold_evidence={}
 for i,label in enumerate(labels):
  threshold=1.01;evidence={'accepted':0,'precision':None}
  if label in ('Garbage / litter','Pothole'):
   for candidate in np.arange(.70,1.,.01):
    chosen=(calibrated.argmax(1)==i)&(calibrated[:,i]>=candidate)&((np.sort(calibrated,axis=1)[:,-1]-np.sort(calibrated,axis=1)[:,-2])>=.15)
    if chosen.sum()>=20 and (val_truth[chosen]==i).mean()>=.90:
     threshold=float(candidate);evidence={'accepted':int(chosen.sum()),'precision':float((val_truth[chosen]==i).mean())};break
  thresholds[label]=threshold;threshold_evidence[label]=evidence
 checkpoint.update({'temperature':temperature,'class_thresholds':thresholds,'review_margin':.15})
 torch.save(checkpoint,model_path)
 test,truth,prob=evaluate(model,loaders['test'],device,labels)
 prob=softmax(np.log(np.clip(prob,1e-12,1))/temperature,axis=1)
 selected=prob.max(1)>=.70
 test_rows=[r for r in rows if r['split']=='test'];group_indices=defaultdict(list)
 for i,row in enumerate(test_rows):group_indices[row['group']].append(i)
 group_truth=[int(truth[indices[0]]) for indices in group_indices.values()]
 group_pred=[int(prob[indices].mean(axis=0).argmax()) for indices in group_indices.values()]
 if args.manifest:
  sample_weights=np.asarray([1/len(group_indices[r['group']]) for r in test_rows])
  group_report=classification_report(truth,prob.argmax(1),sample_weight=sample_weights,labels=list(range(len(labels))),target_names=labels,output_dict=True,zero_division=0)
 else:group_report=classification_report(group_truth,group_pred,labels=list(range(len(labels))),target_names=labels,output_dict=True,zero_division=0)
 result={'architecture':'MobileNetV3-Small','pretraining':'torchvision ImageNet1K V1','training':'2 classifier warm-up epochs then full CNN fine-tuning; AdamW; weighted cross-entropy; train-only crop, horizontal flip, color jitter; best validation macro F1 checkpoint; 768px long-edge lossless PNG cache (one per original, not extra examples)','seed':SEED,'device':str(device),'epochs_run':len(history),'best_epoch':best_epoch,'history':history,'audit':audit,'splits':dict(Counter(r['split'] for r in rows)),'validation':val,'test':test,'review_threshold':.70,'threshold_policy':'Fixed prototype threshold, not calibrated','test_threshold_coverage':float(selected.mean()),'test_accuracy_above_threshold':float((prob.argmax(1)[selected]==truth[selected]).mean()) if selected.any() else None,'source':SOURCE,'training_seconds':round(time.time()-started,1),'limitations':'Single-label scene classification, not object detection. Folder labels and heterogeneous sources can introduce shortcuts. No normal/healthy or arbitrary-image rejection class; confidence alone cannot reject all unsupported images. No verified Lucknow image holdout. Parking legality, urgency, water supply and streetlight operation cannot be established from this model. Dataset listing MIT conflicts with description CC0 and upstream terms; raw images are for local evaluation and are excluded from review package pending provenance clearance.','manifest_sha256':hashlib.sha256((artifact_dir/'manifest.csv').read_bytes()).hexdigest()}
 result['test_group_report']=group_report
 result['group_evaluation']='Average class probabilities within each held-out source/perceptual group, then one prediction per group. This prevents groups with many augmented copies dominating the summary.'
 result['manifest_sha256']=hashlib.sha256((artifact_dir/'manifest.csv').read_bytes()).hexdigest()
 result['calibration']={'temperature':temperature,'validation_nll_before':objective(1.),'validation_nll_after':objective(temperature),'class_thresholds':thresholds,'validation_threshold_evidence':threshold_evidence,'policy':'Temperature minimizes validation negative log likelihood. Garbage/litter and pothole thresholds require >=90% observed validation precision on >=20 accepted validation images, minimum score .70 and top-two margin .15. Other classes always require review. These are in-distribution checks, not guarantees on arbitrary uploads.'}
 approved=np.array([prob[i].max()>=thresholds[labels[int(prob[i].argmax())]] and np.sort(prob[i])[-1]-np.sort(prob[i])[-2]>=.15 for i in range(len(prob))])
 result['selective_test']={'coverage':float(approved.mean()),'accepted':int(approved.sum()),'precision':float((prob[approved].argmax(1)==truth[approved]).mean()) if approved.any() else None}
 result['model_sha256']=hashlib.sha256(model_path.read_bytes()).hexdigest()
 result['torch_version']=torch.__version__;result['parameters']=sum(p.numel() for p in model.parameters())
 result['additional_source']='https://github.com/garythung/trashnet'
 result['outdoor_litter_source']='https://github.com/pedropro/TACO'
 result['modelVersion']=args.version
 result['architecture']='MobileNetV3-Large' if args.architecture=='mobilenet_v3_large' else 'MobileNetV3-Small'
 result['pretraining']='torchvision ImageNet1K V2' if args.architecture=='mobilenet_v3_large' else 'torchvision ImageNet1K V1'
 result['image_size']=args.image_size;result['batch_size']=args.batch_size
 if args.preserve_frame:result['training']=result['training'].replace('train-only crop, horizontal flip, color jitter','full-frame resize, train-only horizontal flip and color jitter (no random crops)')
 result['label_audit']='TACO annotated outdoor-litter photographs and TrashNet material photos form Garbage / litter. Original road-dataset street-litter folder remains Street scene / review because spot checks did not establish garbage incidents. Images with >18% near-black thumbnail pixels excluded. Full photos are used; this is scene classification, not litter localization.'
 if args.manifest:
  result['sources']=audit['sources'];result['source']=audit['sources'][0]['url']
  result.pop('additional_source',None);result.pop('outdoor_litter_source',None)
  result['label_audit']=audit['label_policy']
  result['limitations']=audit['limitations']
  result['threshold_policy']=result['calibration']['policy']
  result['group_evaluation']='Each test image receives weight 1 / number of images in its source group. Each group contributes total weight one. Labels remain per image because a road sequence can contain several different conditions.'
  result['group_evaluation_method']='inverse_group_size_weights'
 (run/'data/image_metrics.json').write_text(json.dumps(result,indent=2));print('FINAL',json.dumps({'test_accuracy':test['report']['accuracy'],'test_macro_f1':test['report']['macro avg']['f1-score'],'splits':result['splits'],'seconds':result['training_seconds']}),flush=True)
if __name__=='__main__':main()
