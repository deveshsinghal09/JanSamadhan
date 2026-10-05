import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'jansamadhan-test-'));
const server=spawn(process.execPath,['backend/server.js'],{env:{...process.env,PORT:'3012',NODE_ENV:'test',ALLOW_DEMO_ACCOUNTS:'true',BOOTSTRAP_ADMIN_EMAIL:'',BOOTSTRAP_ADMIN_PASSWORD:'',DATA_DIR:dir,LOAD_DOTENV:'false',DATABASE_URL:'',MONGODB_URI:''},stdio:'pipe'});
let output='';server.stderr.on('data',d=>{output+=d;process.stderr.write(d)});
const base='http://127.0.0.1:3012/api';
const imageMetrics=JSON.parse(fs.readFileSync(fs.existsSync('ml/image_pipeline.json')?'data/image_pipeline_metrics.json':'data/image_metrics.json','utf8'));
async function request(p,{cookie,method='GET',body}={}){const r=await fetch(base+p,{method,headers:{...(cookie?{Cookie:cookie}:{}),...(body instanceof FormData?{}:{'Content-Type':'application/json'})},body:body?body instanceof FormData?body:JSON.stringify(body):undefined});return {status:r.status,data:await r.json(),cookie:r.headers.get('set-cookie')?.split(';')[0]};}
let citizen,admin,officer,roads,created,firstReport;
test.before(async()=>{const ai=await fetch('http://127.0.0.1:8001/health').then(r=>r.json());assert.equal(ai.version,'2.0','Restart the AI service to load model v2');for(let i=0;i<50;i++){try{await fetch(base+'/health');return}catch{await new Promise(r=>setTimeout(r,200))}}throw Error(output)});
test.after(()=>{server.kill();});
test('anonymous requests cannot read complaints',async()=>{assert.equal((await request('/complaints')).status,401)});
test('valid demo users authenticate and invalid credentials fail',async()=>{for(const [id,assign] of [['citizen',x=>citizen=x],['admin',x=>admin=x],['sanitation',x=>officer=x],['roads',x=>roads=x]]){const r=await request('/auth/login',{method:'POST',body:{email:id+'@demo.in',password:'Review@123'}});assert.equal(r.status,200);assign(r.cookie)}assert.equal((await request('/auth/login',{method:'POST',body:{email:'citizen@demo.in',password:'wrong'}})).status,401)});
test('registration cannot self-elevate to administrator',async()=>{let r=await request('/auth/register',{method:'POST',body:{name:'Test citizen',email:'test@example.test',password:'Testing123',role:'admin'}});assert.equal(r.status,201);r=await request('/auth/login',{method:'POST',body:{email:'test@example.test',password:'Testing123'}});assert.equal(r.data.role,'citizen');assert.equal((await request('/complaints',{cookie:r.cookie})).data.length,0)});
test('image analysis requires login, rejects invalid files and returns model scores',async()=>{
 const photo=()=>{const f=new FormData();f.append('image',new Blob([fs.readFileSync('tests/fixtures/image.png')],{type:'image/png'}),'image.png');return f;};
 assert.equal((await request('/predict-image',{method:'POST',body:photo()})).status,401);
 const bad=new FormData();bad.append('image',new Blob(['not an image'],{type:'image/png'}),'bad.png');
 assert.equal((await request('/predict-image',{method:'POST',cookie:citizen,body:bad})).status,400);
 const result=await request('/predict-image',{method:'POST',cookie:citizen,body:photo()});assert.equal(result.status,200);assert.equal(result.data.modelVersion,imageMetrics.modelVersion);assert.equal(Object.keys(result.data.scores).length,imageMetrics.test.labels.length);assert.ok(result.data.confidence>=0&&result.data.confidence<=1);
});
test('starts without seeded complaints and previews a real submitted repeat',async()=>{
 const payload={description:'Garbage has not been collected near the market for three days.',locality:'Hazratganj',lat:26.8467,lng:80.9462};
 assert.equal((await request('/complaints',{cookie:citizen})).data.length,0);
 const preview=await request('/predict',{method:'POST',cookie:citizen,body:payload});assert.equal(preview.status,200);assert.equal(preview.data.prediction.category,'Garbage');assert.equal(preview.data.duplicates.matches.length,0);
 const f=new FormData();Object.entries(payload).forEach(([k,v])=>f.append(k,v));const saved=await request('/complaints',{method:'POST',cookie:citizen,body:f});assert.equal(saved.status,201);firstReport=saved.data;
 const repeated=await request('/predict',{method:'POST',cookie:citizen,body:payload});assert.equal(repeated.status,200);assert.ok(repeated.data.duplicates.matches.some(c=>c.id===firstReport.id));
});

test('external pothole photo with road description is never routed as water supply',async()=>{
 const form=new FormData();Object.entries({description:'There is a deep pothole and broken asphalt in the municipal road. Please repair the damaged road.',locality:'Hazratganj',lat:26.8467,lng:80.9462}).forEach(([k,v])=>form.append(k,v));
 form.append('image',new Blob([fs.readFileSync('tests/fixtures/external-pothole.jpg')],{type:'image/jpeg'}),'pothole.jpg');
 const r=await request('/predict',{method:'POST',cookie:citizen,body:form});
 assert.equal(r.status,200);assert.equal(r.data.prediction.category,'Road Damage');assert.equal(r.data.prediction.decisionMethod,'text-image-consensus-v1');
 assert.equal(r.data.prediction.evidence.photoLabel,r.data.imagePrediction.label);
 if(r.data.imagePrediction.label==='Waterlogging / flooded road'&&r.data.imagePrediction.confidence>=.7){assert.equal(r.data.prediction.manualReview,true);assert.equal(r.data.prediction.evidence.status,'conflict');}
});

test('rejects outside-pilot coordinates',async()=>{const r=await request('/predict',{method:'POST',cookie:citizen,body:{description:'Garbage collection is delayed.',locality:'Hazratganj',lat:28.6,lng:77.2}});assert.equal(r.status,400)});
test('persists report, image and duplicate acknowledgement',async()=>{const f=new FormData();Object.entries({description:'Garbage has not been collected near the market for three days.',locality:'Hazratganj',lat:26.8467,lng:80.9462,linkDuplicate:true}).forEach(([k,v])=>f.append(k,v));f.append('image',new Blob([fs.readFileSync('tests/fixtures/image.png')],{type:'image/png'}),'pixel.png');const preview=await request('/predict',{method:'POST',cookie:citizen,body:f});assert.equal(preview.status,200);assert.equal(preview.data.prediction.decisionMethod,'text-image-consensus-v1');assert.ok(preview.data.imagePrediction);const r=await request('/complaints',{method:'POST',cookie:citizen,body:f});assert.equal(r.status,201);created=r.data;assert.deepEqual(created.prediction.evidence,preview.data.prediction.evidence);assert.equal(created.category,preview.data.prediction.category);assert.equal(created.department,created.prediction.manualReview?'review':'sanitation');assert.ok(created.duplicateOf);assert.equal(created.imagePrediction.modelVersion,imageMetrics.modelVersion);assert.ok(created.imagePrediction.agreement);assert.ok(fs.existsSync(path.join(dir,'uploads',created.image)));const saved=JSON.parse(fs.readFileSync(path.join(dir,'db.json'),'utf8'));assert.ok(saved.complaints.some(c=>c.id===created.id));const img=await fetch(base+'/complaints/'+created.id+'/image',{headers:{Cookie:citizen}});assert.equal(img.status,200);assert.match(img.headers.get('content-type'),/image\/png/)});
test('officer sees only own department and cannot access another image or case',async()=>{const list=await request('/complaints',{cookie:roads});assert.ok(list.data.every(c=>c.department==='roads'));assert.equal((await request('/complaints/'+created.id,{cookie:roads,method:'PATCH',body:{status:'In Progress',note:'Test cross department'}})).status,404);assert.equal((await fetch(base+'/complaints/'+created.id+'/image',{headers:{Cookie:roads}})).status,404)});
test('citizen cannot update status and officer cannot skip work',async()=>{assert.equal((await request('/complaints/'+created.id,{cookie:citizen,method:'PATCH',body:{status:'Resolved',note:'Please resolve'}})).status,403);assert.equal((await request('/complaints/'+created.id,{cookie:officer,method:'PATCH',body:{status:'Resolved',note:'Skipped inspection'}})).status,400)});
test('officer progresses and resolves with audit trail; administrator can reopen',async()=>{for(const status of ['In Progress','Resolved']){const r=await request('/complaints/'+created.id,{cookie:officer,method:'PATCH',body:{status,note:'Functional test action recorded'}});assert.equal(r.status,200);assert.equal(r.data.status,status)}const r=await request('/complaints/'+created.id,{cookie:admin,method:'PATCH',body:{status:'In Progress',note:'Reopened following citizen feedback'}});assert.equal(r.status,200);assert.equal(r.data.history.at(-1).status,'In Progress')});
test('priority corrections are scoped, validated and preserve raw model evidence',async()=>{
 const p='/complaints/'+created.id;
 for(const [cookie,expected] of [[citizen,403],[roads,404]])assert.equal((await request(p,{cookie,method:'PATCH',body:{urgency:'High',note:'Priority review'}})).status,expected);
 assert.equal((await request(p,{cookie:officer,method:'PATCH',body:{urgency:'Invalid',note:'Priority review'}})).status,400);
 assert.equal((await request(p,{cookie:officer,method:'PATCH',body:{urgency:'High',status:'Resolved',note:'Priority review'}})).status,400);
 const r=await request(p,{cookie:officer,method:'PATCH',body:{urgency:'High',note:'Inspection found a safety risk'}});
 assert.equal(r.status,200);assert.equal(r.data.urgency,'High');assert.equal(r.data.status,'In Progress');assert.deepEqual(r.data.prediction,created.prediction);assert.match(r.data.history.at(-1).note,/Priority changed from .* to High/);
 const stored=JSON.parse(fs.readFileSync(path.join(dir,'db.json'),'utf8')).complaints.find(c=>c.id===created.id);assert.equal(stored.urgency,'High');
});
test('out-of-jurisdiction complaint requires administrator routing',async()=>{const f=new FormData();Object.entries({description:'National highway has a large pothole requiring repairs.',locality:'Aliganj',lat:26.898,lng:80.945}).forEach(([k,v])=>f.append(k,v));const r=await request('/complaints',{method:'POST',cookie:citizen,body:f});assert.equal(r.data.status,'Needs Review');assert.equal(r.data.department,'review');const moved=await request('/complaints/'+r.data.id,{method:'PATCH',cookie:admin,body:{department:'roads',note:'Test only: ownership verified as municipal road'}});assert.equal(moved.data.department,'roads');assert.equal(moved.data.status,'Assigned')});
test('spoofed image rejected',async()=>{const f=new FormData();Object.entries({description:'Garbage collection is delayed again.',locality:'Aliganj',lat:26.898,lng:80.945}).forEach(([k,v])=>f.append(k,v));f.append('image',new Blob(['<script>alert(1)</script>'],{type:'image/png'}),'bad.png');assert.equal((await request('/complaints',{method:'POST',cookie:citizen,body:f})).status,400)});
test('cross-origin mutation denied and logout invalidates session',async()=>{const r=await fetch(base+'/auth/logout',{method:'POST',headers:{Origin:'https://untrusted.example',Cookie:citizen}});assert.equal(r.status,403);await request('/auth/logout',{method:'POST',cookie:citizen});assert.equal((await request('/complaints',{cookie:citizen})).status,401)});

