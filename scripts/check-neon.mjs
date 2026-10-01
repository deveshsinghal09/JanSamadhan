import dotenv from 'dotenv';
import {PostgresStore} from '../backend/postgres.js';
dotenv.config({quiet:true});
if(!process.env.DATABASE_URL)throw Error('Set DATABASE_URL in .env first');
const store=new PostgresStore(process.env.DATABASE_URL);
try{
 const reports=await store.pool.query("SELECT count(*)::int AS reports,count(*) FILTER (WHERE data->>'isSynthetic'='true')::int AS seeded FROM jansamadhan.complaints");
 const users=await store.pool.query('SELECT count(*)::int AS users FROM jansamadhan.users');
 const photos=await store.pool.query('SELECT count(*)::int AS photos FROM jansamadhan.photos');
 console.log({...reports.rows[0],...users.rows[0],...photos.rows[0]});
 console.log(await fetch('http://127.0.0.1:3001/api/health').then(r=>r.json()));
}finally{await store.close();}
