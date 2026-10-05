import pg from 'pg';
import fs from 'node:fs';
import path from 'node:path';
export class PostgresStore {
 constructor(connectionString){
  const url=new URL(connectionString);
  for(const key of ['sslmode','sslcert','sslkey','sslrootcert'])url.searchParams.delete(key);
  this.pool=new pg.Pool({connectionString:url.toString(),ssl:{rejectUnauthorized:true},max:3,connectionTimeoutMillis:10000,idleTimeoutMillis:30000,query_timeout:12000,statement_timeout:10000});
  this.pool.on('error',()=>console.error('Database connection interrupted; the next request will reconnect.'));
 }
 async init(){await this.pool.query(`CREATE SCHEMA IF NOT EXISTS jansamadhan;
  CREATE TABLE IF NOT EXISTS jansamadhan.users(id text PRIMARY KEY,email text UNIQUE NOT NULL,name text NOT NULL,password_hash text NOT NULL,role text NOT NULL,department text);
  CREATE TABLE IF NOT EXISTS jansamadhan.complaints(id text PRIMARY KEY,user_id text NOT NULL REFERENCES jansamadhan.users(id),department text NOT NULL,status text NOT NULL,created_at timestamptz NOT NULL,updated_at timestamptz NOT NULL,data jsonb NOT NULL);
  CREATE INDEX IF NOT EXISTS complaints_user_idx ON jansamadhan.complaints(user_id);
  CREATE INDEX IF NOT EXISTS complaints_department_status_idx ON jansamadhan.complaints(department,status);
  CREATE TABLE IF NOT EXISTS jansamadhan.photos(complaint_id text PRIMARY KEY REFERENCES jansamadhan.complaints(id) ON DELETE CASCADE,filename text NOT NULL,content_type text NOT NULL,bytes bytea NOT NULL);
  CREATE TABLE IF NOT EXISTS jansamadhan.sessions(token_hash text PRIMARY KEY,user_id text NOT NULL REFERENCES jansamadhan.users(id) ON DELETE CASCADE,expires_at timestamptz NOT NULL);
  CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON jansamadhan.sessions(expires_at);`);}
 async load(client=this.pool){
  const users=await client.query('SELECT id,email,name,password_hash AS password,role,department FROM jansamadhan.users');
  const complaints=await client.query('SELECT data FROM jansamadhan.complaints ORDER BY created_at');
  return {users:users.rows,complaints:complaints.rows.map(r=>r.data)};
 }
 async change(change,photo,runtime){
  const client=await this.pool.connect();
  try{
   await client.query('BEGIN');
   await client.query("SELECT pg_advisory_xact_lock(hashtext('jansamadhan-state'))");
   const previous=await this.load(client),next=structuredClone(previous);
   const value=await change(next);
   await this.save(next,previous,photo,runtime,client);
   await client.query('COMMIT');return {next,value};
  }catch(error){await client.query('ROLLBACK').catch(()=>{});throw error}finally{client.release()}
 }
 async save(next,previous={users:[],complaints:[]},photo,runtime,transactionClient){
  const client=transactionClient||await this.pool.connect();
  try{
   if(!transactionClient)await client.query('BEGIN');
   const oldUsers=new Map(previous.users.map(u=>[u.id,JSON.stringify(u)]));
   for(const u of next.users){if(oldUsers.get(u.id)===JSON.stringify(u))continue;
    await client.query(`INSERT INTO jansamadhan.users(id,email,name,password_hash,role,department) VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(id) DO UPDATE SET email=EXCLUDED.email,name=EXCLUDED.name,password_hash=EXCLUDED.password_hash,role=EXCLUDED.role,department=EXCLUDED.department`,[u.id,u.email,u.name,u.password,u.role,u.department||null]);
   }
   const oldReports=new Map(previous.complaints.map(c=>[c.id,JSON.stringify(c)]));
   for(const c of next.complaints){if(oldReports.get(c.id)===JSON.stringify(c))continue;
    await client.query(`INSERT INTO jansamadhan.complaints(id,user_id,department,status,created_at,updated_at,data) VALUES($1,$2,$3,$4,$5,$6,$7::jsonb) ON CONFLICT(id) DO UPDATE SET department=EXCLUDED.department,status=EXCLUDED.status,updated_at=EXCLUDED.updated_at,data=EXCLUDED.data`,[c.id,c.userId,c.department,c.status,c.createdAt,c.updatedAt,JSON.stringify(c)]);
    if(c.image&&!oldReports.has(c.id)&&(!photo||photo.id!==c.id)){
     const file=path.join(runtime,'uploads',path.basename(c.image));
     if(fs.existsSync(file))await this.putPhoto(client,{id:c.id,filename:c.image,contentType:c.image.endsWith('.png')?'image/png':'image/jpeg',buffer:fs.readFileSync(file)});
    }
   }
   if(photo)await this.putPhoto(client,photo);
   const ids=new Set(next.complaints.map(c=>c.id));
   for(const old of previous.complaints)if(!ids.has(old.id))await client.query('DELETE FROM jansamadhan.complaints WHERE id=$1',[old.id]);
   if(!transactionClient)await client.query('COMMIT');
  }catch(error){if(!transactionClient)await client.query('ROLLBACK').catch(()=>{});throw error;}finally{if(!transactionClient)client.release();}
 }
 async putPhoto(client,p){await client.query('INSERT INTO jansamadhan.photos(complaint_id,filename,content_type,bytes) VALUES($1,$2,$3,$4) ON CONFLICT(complaint_id) DO UPDATE SET filename=EXCLUDED.filename,content_type=EXCLUDED.content_type,bytes=EXCLUDED.bytes',[p.id,p.filename,p.contentType,p.buffer]);}
 async photo(id){return (await this.pool.query('SELECT content_type,bytes FROM jansamadhan.photos WHERE complaint_id=$1',[id])).rows[0];}
 async health(){await this.pool.query('SELECT 1');return true;}
 async close(){await this.pool.end();}
}
