import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import dotenv from 'dotenv';
import {PostgresStore} from './postgres.js';
export const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
if(process.env.LOAD_DOTENV!=='false')dotenv.config({path:path.join(root,'.env'),quiet:true});
export const runtime=process.env.DATA_DIR || path.join(root,'data/runtime');
fs.mkdirSync(runtime,{recursive:true});
const file=path.join(runtime,'db.json');
let postgres,queue=Promise.resolve();
export let db = {users:[], complaints:[], sessions:[]};
export const demoAccountsEnabled = process.env.NODE_ENV === 'test' && process.env.ALLOW_DEMO_ACCOUNTS === 'true';
export const isDisabledAccount = u => !demoAccountsEnabled && (u.id === 'admin-demo' || u.id === 'citizen-demo' || u.id.startsWith('officer-') || u.email.endsWith('@demo.in'));
export const storageMode=process.env.DATABASE_URL ? 'Neon PostgreSQL' : 'Local persistent storage';
export function passwordHash(password,salt=crypto.randomBytes(16).toString('hex')){return salt+':'+crypto.scryptSync(password,salt,64).toString('hex');}
export function verifyPassword(password,hash){if(typeof hash!=='string')return false;const [salt]=hash.split(':');const actual=Buffer.from(passwordHash(password,salt)),expected=Buffer.from(hash);return actual.length===expected.length&&crypto.timingSafeEqual(actual,expected);}
function writeLocal(state,photo){
 if(photo){fs.mkdirSync(path.join(runtime,'uploads'),{recursive:true});fs.writeFileSync(path.join(runtime,'uploads',photo.filename),photo.buffer);}
 fs.writeFileSync(file+'.tmp',JSON.stringify(state,null,2));fs.renameSync(file+'.tmp',file);
}
export function mutate(change,photo){
 const work=queue.then(async()=>{if(postgres){const {next,value}=await postgres.change(change,photo,runtime);db=next;return value}const next=structuredClone(db);const value=await change(next);writeLocal(next,photo);db=next;return value;});
 queue=work.catch(()=>{});return work;
}
export async function databaseHealth(){if(postgres)return postgres.health();return true;}
export async function readPhoto(c){if(postgres)return postgres.photo(c.id);const p=path.join(runtime,'uploads',path.basename(c.image));return fs.existsSync(p)?{bytes:fs.readFileSync(p),content_type:c.image.endsWith('.png')?'image/png':'image/jpeg'}:null;}
export async function closeStore(){await queue;if(postgres)await postgres.close();}
const tokenHash = token => crypto.createHash('sha256').update(token).digest('hex');
export async function createSession(token, userId, expires) {
 const session={token:tokenHash(token),id:userId,expires};
 if(postgres){await postgres.pool.query('DELETE FROM jansamadhan.sessions WHERE expires_at < now()');await postgres.pool.query('INSERT INTO jansamadhan.sessions(token_hash,user_id,expires_at) VALUES($1,$2,$3)',[session.token,userId,new Date(expires)]);}
 else await mutate(state=>{state.sessions=(state.sessions||[]).filter(s=>s.expires>Date.now());state.sessions.push(session)});
}
export async function refreshStore(){
 if(!postgres)return;
 const work=queue.then(async()=>{db=await postgres.load()});queue=work.catch(()=>{});await work;
}
export async function findSession(token) {
 if(typeof token!=='string'||!/^[a-f0-9]{64}$/.test(token))return null;
 if(postgres)return (await postgres.pool.query('SELECT user_id AS id FROM jansamadhan.sessions WHERE token_hash=$1 AND expires_at>now()',[tokenHash(token)])).rows[0];
 return db.sessions?.find(s=>s.token===tokenHash(token)&&s.expires>Date.now());
}
export async function deleteSession(token) {
 if(typeof token!=='string')return;
 if(postgres)await postgres.pool.query('DELETE FROM jansamadhan.sessions WHERE token_hash=$1',[tokenHash(token)]);
 else await mutate(state=>{state.sessions=(state.sessions||[]).filter(s=>s.token!==tokenHash(token))});
}
export async function init(directory){
 let original;
 if(process.env.DATABASE_URL){if(postgres)await postgres.close();postgres=new PostgresStore(process.env.DATABASE_URL);await postgres.init();original=await postgres.load();}
 const local=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):null;
 db=structuredClone(original?.users.length?original:local);
 if(!db){db={users:[],complaints:[],sessions:[]};if(demoAccountsEnabled){const password=passwordHash('Review@123');db.users=[{password,id:'citizen-demo',name:'Test citizen',email:'citizen@demo.in',role:'citizen'},{password,id:'admin-demo',name:'Test administrator',email:'admin@demo.in',role:'admin'},...directory.departments.map(d=>({password,id:'officer-'+d.id,name:d.officer,email:d.id+'@demo.in',role:'officer',department:d.id}))];}}
 const adminEmail=process.env.BOOTSTRAP_ADMIN_EMAIL?.trim().toLowerCase(),adminPassword=process.env.BOOTSTRAP_ADMIN_PASSWORD;
 if(adminEmail&&adminPassword){
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(adminEmail)||adminEmail.endsWith('@demo.in')||adminPassword.length<12)throw Error('Administrator setup requires a real email and a password of at least 12 characters');
  const existing=db.users.find(u=>u.email===adminEmail);
  if(existing&&existing.role!=='admin')throw Error('Administrator email already belongs to a non-administrator; review ownership before provisioning');
  if(!existing)db.users.push({id:crypto.randomUUID(),name:'Administrator',email:adminEmail,password:passwordHash(adminPassword),role:'admin'});
 }
 const before=structuredClone(db);const removed=db.complaints.filter(c=>c.isSynthetic===true);
 if(removed.length){const backup=path.join(runtime,'backups');fs.mkdirSync(backup,{recursive:true});fs.writeFileSync(path.join(backup,'before-seed-removal-'+Date.now()+'.json'),JSON.stringify(before,null,2));db.complaints=db.complaints.filter(c=>c.isSynthetic!==true);console.log(`Removed ${removed.length} seeded reports; preserved ${db.complaints.length} submitted reports. Backup saved locally.`);}
 if(postgres)await postgres.save(db,original,undefined,runtime);else writeLocal(db);
}
