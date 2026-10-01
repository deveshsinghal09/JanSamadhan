import {combineEvidence} from './evidence.js';
import express from 'express';
import cookieParser from 'cookie-parser';
import multer from 'multer';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {root,runtime,db,init,mutate,passwordHash,verifyPassword,storageMode,databaseHealth,readPhoto} from './store.js';
const directory=JSON.parse(fs.readFileSync(path.join(root,'data/directory.json'),'utf8'));
await init(directory);
const app=express();const sessions=new Map(),attempts=new Map();
const aiServiceUrl=(process.env.AI_SERVICE_URL||'http://127.0.0.1:8001').replace(/\/$/,'');
const publicOrigins=new Set((process.env.PUBLIC_ORIGINS||'').split(',').map(x=>x.trim()).filter(Boolean));
if(process.env.NODE_ENV==='production')app.set('trust proxy',1);
app.disable('x-powered-by');app.use(express.json({limit:'32kb'}));app.use(cookieParser());
app.use((req,res,next)=>{res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','same-origin');const origin=req.headers.origin,ownOrigin=`${req.protocol}://${req.headers.host}`;if(['POST','PATCH','DELETE'].includes(req.method)&&origin&&origin!==ownOrigin&&!publicOrigins.has(origin))return res.status(403).json({error:'Cross-origin writes are blocked'});next();});
const publicUser=u=>({id:u.id,name:u.name,email:u.email,role:u.role,department:u.department});
const fail=(res,code,error)=>res.status(code).json({error});
const reject=(status,message)=>{throw Object.assign(new Error(message),{status});};
app.get('/api/health',async(req,res)=>{let ai=false;try{ai=(await fetch(aiServiceUrl+'/health',{signal:AbortSignal.timeout(2000)})).ok;}catch{}let database=false;try{database=await databaseHealth()}catch{}res.json({status:database&&ai?'ok':'degraded',ai,database,storage:storageMode});});
app.get('/api/directory',(req,res)=>res.json(directory));
app.get('/api/metrics',(req,res)=>res.sendFile(path.join(root,'data/model_metrics.json')));
app.get('/api/image-metrics',(req,res)=>{const file=path.join(root,fs.existsSync(path.join(root,'ml/image_pipeline.json'))?'data/image_pipeline_metrics.json':'data/image_metrics.json');if(!fs.existsSync(file))return fail(res,503,'Image training has not completed yet');res.sendFile(file);});
app.get('/api/dataset',(req,res)=>res.download(path.join(root,'data/training_complaints.csv')));
app.post('/api/auth/login',(req,res)=>{const key=req.ip;let a=attempts.get(key);if(!a||a.until<Date.now())a={count:0,until:Date.now()+60000};attempts.set(key,a);if(++a.count>30)return fail(res,429,'Too many attempts. Wait one minute.');const {email,password}=req.body;if(typeof email!=='string'||typeof password!=='string'||password.length>128)return fail(res,400,'Enter email and password');const u=db.users.find(x=>x.email===email.toLowerCase().trim());if(!u||!verifyPassword(password,u.password))return fail(res,401,'Incorrect email or password');const token=crypto.randomBytes(32).toString('hex');sessions.set(token,{id:u.id,expires:Date.now()+8*3600000});res.cookie('session',token,{httpOnly:true,sameSite:'strict',maxAge:8*3600000,secure:process.env.NODE_ENV==='production'});res.json(publicUser(u));});
app.post('/api/auth/register',async(req,res)=>{const {name,email,password}=req.body;if(typeof name!=='string'||name.trim().length<2||name.length>80||typeof email!=='string'||! /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||email.length>120||typeof password!=='string'||password.length<8||password.length>128)return fail(res,400,'Provide name, valid email and an 8–128 character password');if(db.users.some(u=>u.email===email.toLowerCase().trim()))return fail(res,409,'Email is already registered');await mutate(state=>{if(state.users.some(u=>u.email===email.toLowerCase().trim()))reject(409,'Email is already registered');state.users.push({id:crypto.randomUUID(),name:name.trim(),email:email.toLowerCase().trim(),password:passwordHash(password),role:'citizen'});});res.status(201).json({ok:true});});
app.post('/api/auth/logout',(req,res)=>{sessions.delete(req.cookies.session);res.clearCookie('session');res.json({ok:true});});
app.use('/api',(req,res,next)=>{const s=sessions.get(req.cookies.session);if(!s||s.expires<Date.now())return fail(res,401,'Please sign in');req.user=db.users.find(u=>u.id===s.id);if(!req.user)return fail(res,401,'Please sign in');next();});
app.get('/api/auth/me',(req,res)=>res.json(publicUser(req.user)));
function allowed(u,c){return u.role==='admin'||u.role==='citizen'&&c.userId===u.id||u.role==='officer'&&c.department===u.department;}
app.get('/api/complaints',(req,res)=>res.json(db.complaints.filter(c=>allowed(req.user,c)).sort((a,b)=>b.createdAt.localeCompare(a.createdAt))));
async function ai(endpoint,body){const r=await fetch(aiServiceUrl+'/'+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),signal:AbortSignal.timeout(30000)});if(!r.ok)throw new Error('AI service rejected request');return r.json();}
function validate(body){return typeof body.description==='string'&&body.description.trim().length>=10&&body.description.length<=3000&&Number.isFinite(Number(body.lat))&&Number.isFinite(Number(body.lng))&&body.lat!==''&&body.lng!==''&&Number(body.lat)>=26.70&&Number(body.lat)<=27.02&&Number(body.lng)>=80.75&&Number(body.lng)<=81.15&&directory.localities.some(p=>p.name===body.locality);}
const upload=multer({storage:multer.memoryStorage(),limits:{fileSize:3*1024*1024,files:1,fields:10}});
async function classifyImage(file){
 const r=await fetch(aiServiceUrl+'/predict-image',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({imageBase64:file.buffer.toString('base64')}),signal:AbortSignal.timeout(30000)});
 const data=await r.json();if(!r.ok){const invalid=[400,422].includes(r.status);const e=new Error(typeof data.detail==='string'?data.detail:invalid?'Upload a valid PNG or JPEG image':'Image analysis unavailable');e.status=invalid?400:503;throw e;}return data;
}
app.post('/api/predict',upload.single('image'),async(req,res)=>{
 if(!validate(req.body))return fail(res,400,'Enter 10–3000 characters and a valid Lucknow pilot location');
 try{
  const text=await ai('predict',{text:req.body.description});
  const imagePrediction=req.file?await classifyImage(req.file):null;
  const prediction=combineEvidence(text,imagePrediction);
  const duplicates=await ai('duplicates',{text:req.body.description,lat:Number(req.body.lat),lng:Number(req.body.lng),category:prediction.category,candidates:db.complaints.map(({id,description,lat,lng,createdAt,category,status})=>({id,description,lat,lng,createdAt,category,status}))});
  res.json({prediction,imagePrediction,duplicates});
 }catch(e){return fail(res,e.status||503,e.status===400?e.message:'Analysis unavailable. Check the services and try again.');}
});
app.post('/api/predict-image',upload.single('image'),async(req,res)=>{
 if(!req.file)return fail(res,400,'Choose a PNG or JPEG photo first');
 try{return res.json(await classifyImage(req.file));}catch(e){return fail(res,e.status||503,e.status===400?e.message:'Image analysis unavailable. Check the AI service.');}
});
app.post('/api/complaints',upload.single('image'),async(req,res)=>{
 if(req.user.role!=='citizen')return fail(res,403,'Only citizens can submit complaints');if(!validate(req.body))return fail(res,400,'Check description and Lucknow location');
 let ext;if(req.file){const b=req.file.buffer;ext=b.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))?'png':b[0]===255&&b[1]===216&&b[2]===255?'jpg':null;if(!ext)return fail(res,400,'Upload a PNG or JPEG image');}
 let prediction,duplicates,imagePrediction;try{prediction=await ai('predict',{text:req.body.description});duplicates=await ai('duplicates',{text:req.body.description,lat:Number(req.body.lat),lng:Number(req.body.lng),category:prediction.category,candidates:db.complaints.map(({id,description,lat,lng,createdAt,category,status})=>({id,description,lat,lng,createdAt,category,status}))});if(req.file)imagePrediction=await classifyImage(req.file);prediction=combineEvidence(prediction,imagePrediction);}catch(e){return fail(res,e.status||503,e.status===400?e.message:'AI service unavailable. Report was not saved; please retry.');}
 const id='JS-'+crypto.randomBytes(5).toString('hex').toUpperCase(),at=new Date().toISOString();
 const department=directory.departments.find(d=>d.category===prediction.category).id;
 const c={id,userId:req.user.id,description:req.body.description.trim(),locality:req.body.locality,lat:Number(req.body.lat),lng:Number(req.body.lng),category:prediction.category,department,urgency:prediction.urgency,status:prediction.manualReview?'Needs Review':'Assigned',createdAt:at,updatedAt:at,isSynthetic:false,prediction,duplicateCandidates:duplicates.matches,history:[{status:'Submitted',at,note:'Citizen submitted report',actor:req.user.name},{status:prediction.manualReview?'Needs Review':'Assigned',at,note:prediction.reason,actor:'AI-assisted triage'}]};
 if(req.body.linkDuplicate==='true'&&duplicates.matches.length){c.duplicateOf=duplicates.matches[0].id;c.history.push({status:c.status,at,note:'Citizen acknowledged likely duplicate '+c.duplicateOf,actor:req.user.name});}
 if(imagePrediction){c.imagePrediction={...imagePrediction,agreement:prediction.evidence.explanation};c.history.push({status:c.status,at,note:prediction.evidence.explanation,actor:'Text and photo review'});}
 if(ext)c.image=id+'.'+ext;
 await mutate(state=>{state.complaints.push(c)},ext?{id,filename:c.image,contentType:ext==='png'?'image/png':'image/jpeg',buffer:req.file.buffer}:undefined);res.status(201).json(c);
});
app.get('/api/complaints/:id/image',async(req,res)=>{const c=db.complaints.find(c=>c.id===req.params.id);if(!c||!allowed(req.user,c))return fail(res,404,'Image not found');if(!c.image)return fail(res,404,'No image');const photo=await readPhoto(c);if(!photo)return fail(res,404,'Image not found');res.type(photo.content_type).send(photo.bytes);});
app.patch('/api/complaints/:id',async(req,res)=>{
 const updated=await mutate(state=>{
  const c=state.complaints.find(c=>c.id===req.params.id);
  if(!c||!allowed(req.user,c))reject(404,'Complaint not found');
  if(req.user.role==='citizen')reject(403,'Officer access required');
  let {status,note,department,urgency}=req.body;
  if(typeof note!=='string'||note.trim().length<5||note.length>1000)reject(400,'Add a 5–1000 character action note');
  if([status,department,urgency].filter(v=>v!==undefined).length!==1)reject(400,'Record one status, department or priority change at a time');
  if(department){
   if(req.user.role!=='admin')reject(403,'Only administrator can reassign');
   const d=directory.departments.find(d=>d.id===department);if(!d)reject(400,'Unknown department');
   c.department=d.id;c.category=d.category;c.status=d.id==='review'?'Needs Review':'Assigned';
  }else if(urgency!==undefined){
   if(!['Low','Medium','High'].includes(urgency))reject(400,'Unknown priority');
   note=`Priority changed from ${c.urgency} to ${urgency}: ${note.trim()}`;c.urgency=urgency;
  }else{
   const transitions={'Assigned':['In Progress'],'In Progress':['Resolved'],'Resolved':['In Progress']};
   if(!transitions[c.status]?.includes(status))reject(400,'Invalid status transition; administrator must route review cases');c.status=status;
  }
  c.updatedAt=new Date().toISOString();c.history.push({status:c.status,at:c.updatedAt,note:note.trim(),actor:req.user.name});return c;
 });res.json(updated);
});
app.use('/api',(req,res)=>fail(res,404,'API route not found'));
app.use(express.static(path.join(root,'dist')));app.get('/{*path}',(req,res)=>res.sendFile(path.join(root,'dist/index.html')));
app.use((err,req,res,next)=>{console.error('Request failed:',err.code||err.status||err.name);return fail(res,err instanceof multer.MulterError?400:err.status||503,err instanceof multer.MulterError?'Image must be PNG/JPEG, maximum 3 MB':err.status?err.message:'Could not save or load data. Check the connection and retry; no successful save was confirmed.');});
const host=process.env.HOST||'127.0.0.1',port=Number(process.env.PORT||3001);
app.listen(port,host,()=>console.log(`JanSamadhan API http://${host}:${port} · ${storageMode}`));
