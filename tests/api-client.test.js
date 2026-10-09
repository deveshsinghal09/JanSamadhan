import {test} from 'node:test';
import assert from 'node:assert/strict';
import {api} from '../frontend/api.js';
test('recovers from Render gateway startup errors',async()=>{let calls=0;const result=await api('/directory',{}, {wait:async()=>{},fetch:async()=>++calls<3?new Response('Starting',{status:502}):Response.json({city:'Lucknow'})});assert.equal(calls,3);assert.equal(result.city,'Lucknow');});
test('does not replay a report submission',async()=>{let calls=0;await assert.rejects(api('/complaints',{method:'POST'}, {fetch:async()=>{calls++;return new Response('Unavailable',{status:502})}}),/temporarily unavailable/);assert.equal(calls,1);});
test('preserves sign-in status and does not retry authorization failures',async()=>{let calls=0;await assert.rejects(api('/auth/me',{}, {fetch:async()=>{calls++;return Response.json({error:'Please sign in'},{status:401})}}),e=>e.status===401);assert.equal(calls,1);});
test('stops after bounded retries when server stays down',async()=>{let calls=0;await assert.rejects(api('/directory',{}, {wait:async()=>{},fetch:async()=>{calls++;throw new TypeError('Failed to fetch')}}),/taking longer/);assert.equal(calls,8);});

test('startup reads tolerate a full free-instance wake-up window',async()=>{
 let calls=0;const waits=[];
 const result=await api('/directory',{}, {wait:async ms=>waits.push(ms),fetch:async()=>++calls<8?new Response('Starting',{status:502}):Response.json({city:'Lucknow'})});
 assert.equal(result.city,'Lucknow');assert.equal(calls,8);
 assert.ok(waits.reduce((a,b)=>a+b,0)>=70000);assert.ok(waits.every(ms=>ms<=15000));
});
test('ordinary reads retain their shorter retry limit',async()=>{
 let calls=0;await assert.rejects(api('/complaints',{}, {wait:async()=>{},fetch:async()=>{calls++;return new Response('Starting',{status:503})}}));
 assert.equal(calls,4);
});
