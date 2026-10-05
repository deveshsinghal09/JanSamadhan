import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {createServer} from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';

test('real account lifecycle, officer authorization, citizen visibility and persistent sessions',async()=>{
 const dataDir=fs.mkdtempSync(path.join(os.tmpdir(),'jansamadhan-accounts-'));
 const password=crypto.randomBytes(24).toString('base64url');
 const mock=createServer(async(req,res)=>{res.setHeader('Content-Type','application/json');res.end(JSON.stringify(req.url==='/predict'?{category:'Road Damage',urgency:'Medium',manualReview:false,reason:'Test classifier',method:'test'}:req.url==='/duplicates'?{matches:[]}:{status:'ok'}))});
 mock.listen(0,'127.0.0.1');await once(mock,'listening');
 let server;
 const start=async()=>{server=spawn(process.execPath,['backend/server.js'],{env:{...process.env,LOAD_DOTENV:'false',DATABASE_URL:'',DATA_DIR:dataDir,NODE_ENV:'test',ALLOW_DEMO_ACCOUNTS:'false',BOOTSTRAP_ADMIN_EMAIL:'owner@example.test',BOOTSTRAP_ADMIN_PASSWORD:password,PORT:'3015',AI_SERVICE_URL:`http://127.0.0.1:${mock.address().port}`},stdio:'pipe'});let output='';server.stderr.on('data',d=>output+=d);for(let i=0;i<100;i++){try{const r=await fetch('http://127.0.0.1:3015/api/health').then(r=>r.json());if(r.database)return}catch{}await new Promise(r=>setTimeout(r,100))}throw Error(output||'Server failed to start')};
 const call=async(p,{cookie,body,method=body?'POST':'GET'}={})=>{const r=await fetch('http://127.0.0.1:3015/api'+p,{method,headers:{'Content-Type':'application/json',...(cookie?{Cookie:cookie}:{})},body:body?JSON.stringify(body):undefined});return {status:r.status,data:await r.json(),cookie:r.headers.get('set-cookie')?.split(';')[0]}};
 const login=email=>call('/auth/login',{body:{email,password}});
 try{
  await start();
  const known=await call('/auth/login',{body:{email:'admin@demo.in',password:'Review@123'}});assert.equal(known.status,401);
  const admin=await login('owner@example.test');assert.equal(admin.data.role,'admin');
  for(const [name,email] of [['Citizen','person@example.test'],['Officer','staff@example.test'],['Other','other@example.test']])assert.equal((await call('/auth/register',{body:{name,email,password,role:'admin'}})).status,201);
  const citizen=await login('person@example.test'),officer=await login('staff@example.test'),other=await login('other@example.test');
  assert.equal(officer.data.role,'citizen');assert.equal((await call('/admin/users',{cookie:citizen.cookie})).status,403);
  assert.equal((await call('/admin/users/'+officer.data.id,{cookie:admin.cookie,method:'PATCH',body:{role:'officer',department:'roads'}})).status,200);
  assert.equal((await call('/auth/me',{cookie:officer.cookie})).data.role,'officer');
  const payload={description:'A deep pothole needs urgent road repairs.',locality:'Hazratganj',lat:26.8467,lng:80.9462};
  const created=await call('/complaints',{cookie:citizen.cookie,body:payload});assert.equal(created.status,201);
  const id=created.data.id;assert.equal((await call('/complaints',{cookie:other.cookie})).data.length,0);
  assert.equal((await call('/complaints',{cookie:officer.cookie})).data.length,1);
  for(const status of ['In Progress','Resolved'])assert.equal((await call('/complaints/'+id,{cookie:officer.cookie,method:'PATCH',body:{status,note:'Inspection and repair details recorded'}})).status,200);
  const resolved=(await call('/complaints',{cookie:citizen.cookie})).data[0];assert.equal(resolved.status,'Resolved');assert.ok(resolved.resolution.note);
  assert.equal((await call('/complaints/'+id,{cookie:citizen.cookie,method:'PATCH',body:{action:'request-review',note:'The pothole remains after the reported repair'}})).data.status,'Needs Review');
  assert.equal((await call('/complaints',{cookie:officer.cookie})).data.length,0);
  assert.equal((await call('/complaints/'+id,{cookie:admin.cookie,method:'PATCH',body:{department:'roads',note:'Ownership verified, return to road engineer'}})).data.status,'Assigned');
  assert.equal((await call('/admin/users/'+officer.data.id,{cookie:admin.cookie,method:'PATCH',body:{role:'citizen'}})).status,200);
  assert.equal((await call('/complaints/'+id,{cookie:officer.cookie,method:'PATCH',body:{status:'In Progress',note:'Access must now be rejected'}})).status,404);
  server.kill();await once(server,'exit');await start();
  assert.equal((await call('/auth/me',{cookie:citizen.cookie})).status,200);
  assert.equal((await call('/complaints',{cookie:citizen.cookie})).data[0].status,'Assigned');
  await call('/auth/logout',{cookie:citizen.cookie,body:{}});assert.equal((await call('/auth/me',{cookie:citizen.cookie})).status,401);
 }finally{server?.kill();mock.closeAllConnections();await new Promise(r=>mock.close(r))}
});
