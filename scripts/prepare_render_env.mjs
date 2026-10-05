// Write only the credentials required by the existing application's replacement host.
// The output is covered by .gitignore, .dockerignore and .vercelignore.
import fs from 'node:fs';
import dotenv from 'dotenv';
const local=dotenv.parse(fs.readFileSync('.env'));
if(!local.DATABASE_URL)throw Error('DATABASE_URL is missing');
const values={DATABASE_URL:local.DATABASE_URL,NODE_ENV:'production',HOST:'0.0.0.0',PORT:'10000',AI_SERVICE_URL:'http://127.0.0.1:8001',PUBLIC_ORIGINS:'https://jansamadhan-eight.vercel.app',OMP_NUM_THREADS:'1',OPENBLAS_NUM_THREADS:'1',MKL_NUM_THREADS:'1'};
for(const key of ['BOOTSTRAP_ADMIN_EMAIL','BOOTSTRAP_ADMIN_PASSWORD'])if(local[key])values[key]=local[key];
fs.writeFileSync('.env.render',Object.entries(values).map(([k,v])=>`${k}=${JSON.stringify(v)}`).join('\n')+'\n');
console.log('Prepared .env.render without printing credentials.');
