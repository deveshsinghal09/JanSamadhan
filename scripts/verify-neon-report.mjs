import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import dotenv from 'dotenv';
import {PostgresStore} from '../backend/postgres.js';
dotenv.config({quiet:true});
const id=process.argv[2];if(!/^JS-[A-Z0-9]+$/.test(id||''))throw Error('Pass the submitted report ID');
const store=new PostgresStore(process.env.DATABASE_URL);
try{
 const row=(await store.pool.query('SELECT data FROM jansamadhan.complaints WHERE id=$1',[id])).rows[0];assert.ok(row,'Report missing from PostgreSQL');
 const login=await fetch('http://127.0.0.1:3001/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'citizen@demo.in',password:'Review@123'})});assert.equal(login.status,200);const cookie=login.headers.get('set-cookie').split(';')[0];
 const reports=await fetch('http://127.0.0.1:3001/api/complaints',{headers:{Cookie:cookie}}).then(r=>r.json());assert.ok(reports.some(c=>c.id===id),'Report missing after API restart');assert.ok(reports.every(c=>!c.isSynthetic));
 const photo=await store.photo(id);assert.ok(photo,'Photo missing from PostgreSQL');
 const response=await fetch(`http://127.0.0.1:3001/api/complaints/${id}/image`,{headers:{Cookie:cookie}});assert.equal(response.status,200);
 const hash=b=>crypto.createHash('sha256').update(b).digest('hex');assert.equal(hash(Buffer.from(await response.arrayBuffer())),hash(photo.bytes));
 console.log({id,visibleAfterRestart:true,photoBytes:photo.bytes.length,photoMatchesPostgres:true,seededReports:0});
}finally{await store.close();}
