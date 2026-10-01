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
export let db;
export const storageMode=process.env.DATABASE_URL ? 'Neon PostgreSQL' : 'Local persistent storage';
export function passwordHash(password,salt=crypto.randomBytes(16).toString('hex')){return salt+':'+crypto.scryptSync(password,salt,64).toString('hex');}
export function verifyPassword(password,hash){if(typeof hash!=='string')return false;const [salt]=hash.split(':');const actual=Buffer.from(passwordHash(password,salt)),expected=Buffer.from(hash);return actual.length===expected.length&&crypto.timingSafeEqual(actual,expected);}
function writeLocal(state,photo){
 if(photo){fs.mkdirSync(path.join(runtime,'uploads'),{recursive:true});fs.writeFileSync(path.join(runtime,'uploads',photo.filename),photo.buffer);}
 fs.writeFileSync(file+'.tmp',JSON.stringify(state,null,2));fs.renameSync(file+'.tmp',file);
}
export function mutate(change,photo){
 const work=queue.then(async()=>{const next=structuredClone(db);const value=await change(next);if(postgres)await postgres.save(next,db,photo,runtime);else writeLocal(next,photo);db=next;return value;});
 queue=work.catch(()=>{});return work;
}
export async function databaseHealth(){if(postgres)return postgres.health();return true;}
export async function readPhoto(c){if(postgres)return postgres.photo(c.id);const p=path.join(runtime,'uploads',path.basename(c.image));return fs.existsSync(p)?{bytes:fs.readFileSync(p),content_type:c.image.endsWith('.png')?'image/png':'image/jpeg'}:null;}
export async function closeStore(){await queue;if(postgres)await postgres.close();}
export async function init(directory){
 let original;
 if(process.env.DATABASE_URL){postgres=new PostgresStore(process.env.DATABASE_URL);await postgres.init();original=await postgres.load();}
 const local=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):null;
 db=structuredClone(original?.users.length?original:local);
 if(!db){const password=passwordHash('Review@123');db={users:[{password,id:'citizen-demo',name:'Review citizen',email:'citizen@demo.in',role:'citizen'},{password,id:'admin-demo',name:'Review administrator',email:'admin@demo.in',role:'admin'},...directory.departments.map(d=>({password,id:'officer-'+d.id,name:d.officer,email:d.id+'@demo.in',role:'officer',department:d.id}))],complaints:[]};}
 const before=structuredClone(db);const removed=db.complaints.filter(c=>c.isSynthetic===true);
 if(removed.length){const backup=path.join(runtime,'backups');fs.mkdirSync(backup,{recursive:true});fs.writeFileSync(path.join(backup,'before-seed-removal-'+Date.now()+'.json'),JSON.stringify(before,null,2));db.complaints=db.complaints.filter(c=>c.isSynthetic!==true);console.log(`Removed ${removed.length} seeded reports; preserved ${db.complaints.length} submitted reports. Backup saved locally.`);}
 if(postgres)await postgres.save(db,original,undefined,runtime);else writeLocal(db);
}
