import test from 'node:test';
import assert from 'node:assert/strict';
import {applyAction,canAccess} from '../backend/workflow.js';
const directory={departments:[{id:'roads',category:'Road Damage'},{id:'sanitation',category:'Garbage'},{id:'review',category:'Other'}]};
const citizen={id:'c1',name:'Citizen',role:'citizen'},officer={id:'o1',name:'Officer',role:'officer',department:'roads'},admin={id:'a1',name:'Administrator',role:'admin'};
const complaint=()=>({id:'r1',userId:'c1',department:'roads',category:'Road Damage',status:'Assigned',urgency:'Medium',updatedAt:'2026-10-01T00:00:00.000Z',history:[],prediction:{manualReview:false}});
const run=(c,u,body)=>applyAction(c,u,{note:'Verified action with supporting details',...body},directory);
test('only owner, department officer and administrator see a complaint',()=>{const c=complaint();assert.ok(canAccess(citizen,c));assert.ok(canAccess(officer,c));assert.ok(canAccess(admin,c));assert.equal(canAccess({...citizen,id:'c2'},c),false);assert.equal(canAccess({...officer,department:'sanitation'},c),false)});
test('officer must start before resolving and cannot reopen resolved work',()=>{const c=complaint();assert.throws(()=>run(c,officer,{status:'Resolved'}),e=>e.status===400);run(c,officer,{status:'In Progress'});run(c,officer,{status:'Resolved'});assert.ok(c.resolution.note);assert.throws(()=>run(c,officer,{status:'In Progress'}),e=>e.status===400)});
test('citizen disputes resolution, administrator routes, officer resumes',()=>{const c=complaint();run(c,officer,{status:'In Progress'});run(c,officer,{status:'Resolved'});run(c,citizen,{action:'request-review'});assert.equal(c.department,'review');assert.equal(c.status,'Needs Review');assert.equal(c.resolutionDisputed,true);assert.throws(()=>run(c,officer,{status:'In Progress'}),e=>e.status===404);run(c,admin,{department:'roads'});assert.equal(c.status,'Assigned');run(c,officer,{status:'In Progress'});assert.equal(c.history.length,5);assert.equal(c.history[2].actorRole,'citizen')});
test('officer can return wrongly routed complaints but cannot assign another department',()=>{const c=complaint();assert.throws(()=>run(c,officer,{department:'sanitation'}),e=>e.status===403);run(c,officer,{action:'request-review'});assert.equal(c.department,'review');assert.equal(c.category,'Road Damage');assert.equal(c.status,'Needs Review')});
test('administrator can clear a legacy review in its current department',()=>{const c=complaint();c.status='Needs Review';run(c,admin,{department:'roads'});assert.equal(c.status,'Assigned');assert.ok(c.routingReview);assert.deepEqual(c.prediction,{manualReview:false})});
test('external referrals require administrator, authority and review state',()=>{const c=complaint();run(c,admin,{action:'request-review'});assert.throws(()=>run(c,admin,{action:'refer'}),e=>e.status===400);run(c,admin,{action:'refer',authority:'PWD Lucknow'});assert.equal(c.status,'Referred');assert.equal(c.referral.authority,'PWD Lucknow');assert.notEqual(c.status,'Resolved');run(c,admin,{status:'Needs Review'});assert.equal(c.status,'Needs Review')});
test('stale updates are rejected and action notes preserve audit state',()=>{const c=complaint();const old=c.updatedAt;run(c,officer,{action:'note',expectedUpdatedAt:old});assert.throws(()=>run(c,admin,{urgency:'High',expectedUpdatedAt:old}),e=>e.status===409);assert.equal(c.urgency,'Medium');assert.equal(c.history[0].before.status,'Assigned')});
test('empty, multiple and no-op actions are rejected',()=>{const c=complaint();assert.throws(()=>run(c,admin,{department:''}),e=>e.status===400);assert.throws(()=>run(c,admin,{department:'roads',urgency:'High'}),e=>e.status===400);assert.throws(()=>run(c,officer,{urgency:'Medium'}),e=>e.status===400);assert.throws(()=>run(c,officer,{status:'In Progress',note:'   '}),e=>e.status===400)});

test('review queue and unassigned records cannot be accessed by officers',()=>{
 const c=complaint();c.department='review';
 assert.equal(canAccess({...officer,department:'review'},c),false);
 c.department=undefined;assert.equal(canAccess({...officer,department:undefined},c),false);
 assert.equal(canAccess(admin,c),true);
});
