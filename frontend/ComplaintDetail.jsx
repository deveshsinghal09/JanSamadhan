import React,{useEffect,useState} from 'react';
import {X} from 'lucide-react';
import {api} from './api.js';
import {ImageResult} from './ImageModel.jsx';

export default function ComplaintDetail({item:c,user,directory,close,onUpdated}) {
 const [note,setNote]=useState(''),[department,setDepartment]=useState(c.department),[priority,setPriority]=useState(c.urgency);
 const [authority,setAuthority]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState('');
 const admin=user.role==='admin',staff=admin||user.role==='officer',active=['Assigned','In Progress'].includes(c.status);
 const d=directory.departments.find(d=>d.id===c.department);
 useEffect(()=>{setDepartment(c.department);setPriority(c.urgency)},[c.id,c.department,c.urgency]);
 useEffect(()=>{const f=e=>{if(e.key==='Escape'&&!busy)close()};document.addEventListener('keydown',f);return()=>document.removeEventListener('keydown',f)},[busy,close]);
 const blocked=busy||note.trim().length<5;
 async function update(body){
  if(busy)return;setBusy(true);setError('');setNotice('');
  try{const saved=await api('/complaints/'+c.id,{method:'PATCH',body:JSON.stringify({...body,note,expectedUpdatedAt:c.updatedAt})});setNote('');setNotice('Update saved. The citizen can see it in the action history.');await onUpdated(saved)}
  catch(e){setError(e.message);if(e.status===409)await onUpdated()}
  finally{setBusy(false)}
 }
 const fmt=d=>new Date(d).toLocaleString('en-IN');
 const next={Assigned:'The department must inspect the issue and start work.','In Progress':'The department is working on the issue. Check the action history for updates.','Needs Review':'An administrator must verify the evidence and responsible department.',Resolved:'The department marked this resolved. If the issue remains, request a review below.',Referred:'This issue requires another authority. Follow the referral guidance below.'}[c.status];
 return <div className="overlay" onClick={()=>!busy&&close()}><section className="detail" role="dialog" aria-modal="true" aria-label={'Report '+c.id} onClick={e=>e.stopPropagation()}>
  <div className="detail-head"><div><p className="eyebrow">COMPLAINT RECORD</p><h2>{c.id}</h2></div><button onClick={close} disabled={busy} aria-label="Close report"><X/></button></div>
  <div className="badge-row"><span className="badge">{c.status}</span><span className="badge">{c.urgency}</span></div>
  <p className="alert">{next}</p><p className="detail-description">{c.description}</p><p className="muted">{c.locality} · {c.lat}, {c.lng}<br/>{fmt(c.createdAt)}</p>
  {c.image&&<img className="evidence-image" alt="Submitted issue evidence" src={'/api/complaints/'+c.id+'/image'}/>}<ImageResult result={c.imagePrediction}/>
  <div className="assigned-box"><span className="eyebrow">RESPONSIBLE QUEUE</span><h3>{d?.name||'Administrator review'}</h3><p>{c.department==='review'?'Awaiting administrator routing':d?.officer}</p><small>{d?.scope}</small></div>
  {c.status==='Referred'&&c.referral&&<div className="alert"><strong>{c.referral.authority}</strong><p>{c.referral.instructions}</p><small>This referral is guidance. No complaint was automatically sent to this authority.</small></div>}
  {c.resolution&&<div className="assigned-box"><strong>{c.status==='Resolved'?'Resolution note':'Previous resolution note'}</strong><p>{c.resolution.note}</p><small>{fmt(c.resolution.at)}</small></div>}
  {c.duplicateCandidates?.length>0&&<p className="alert warning">{c.duplicateOf?'Linked repeat of '+c.duplicateOf:'Possible repeat of one of your reports: '+c.duplicateCandidates.map(m=>m.id).join(', ')}. Each report remains individually tracked.</p>}
  <details><summary>Original AI assessment</summary><p>{c.prediction?.reason}</p><small>Original category: {c.prediction?.modelCategory||c.prediction?.category}. Staff decisions and current routing are recorded separately below.</small></details>
  <h3>Action history</h3><div className="timeline">{c.history.map((h,i)=><div key={i}><span/><strong>{h.status}</strong><small>{fmt(h.at)} · {h.actor}</small><p>{h.note}</p></div>)}</div>
  {(staff||c.status==='Resolved')&&<div className="action-form"><h3>{staff?'Record an action':'Issue still unresolved?'}</h3>
   <label>{staff?'Action note (visible to the citizen)':'Explain why another review is needed'}<textarea minLength={5} maxLength={1000} disabled={busy} value={note} onChange={e=>setNote(e.target.value)} placeholder="Describe the inspection, work completed, or reason for review."/></label>
   {error&&<p role="alert" className="error-text">{error}</p>}{notice&&<p role="status">{notice}</p>}
   {staff&&active&&<><button className="primary full" disabled={blocked} onClick={()=>update({status:c.status==='Assigned'?'In Progress':'Resolved'})}>{c.status==='Assigned'?'Start work':'Resolve with this completion note'}</button><button className="secondary full" disabled={blocked} onClick={()=>update({action:'request-review'})}>Return to administrator for review</button></>}
   {user.role==='citizen'&&c.status==='Resolved'&&<button className="primary full" disabled={blocked} onClick={()=>update({action:'request-review'})}>Request administrator review</button>}
   {admin&&['Resolved','Referred'].includes(c.status)&&<button className="primary full" disabled={blocked} onClick={()=>update({status:'Needs Review'})}>Reopen for review</button>}
   {staff&&<button className="secondary full" disabled={blocked} onClick={()=>update({action:'note'})}>Post progress update</button>}
   {staff&&!['Resolved','Referred'].includes(c.status)&&<><label>Priority<select disabled={busy} value={priority} onChange={e=>setPriority(e.target.value)}>{['Low','Medium','High'].map(p=><option key={p}>{p}</option>)}</select></label><button className="secondary full" disabled={blocked||priority===c.urgency} onClick={()=>update({urgency:priority})}>Save priority correction</button></>}
   {admin&&!['Resolved','Referred'].includes(c.status)&&<><label>Assign department<select disabled={busy} value={department} onChange={e=>setDepartment(e.target.value)}>{directory.departments.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label><button className="secondary full" disabled={blocked||(department===c.department&&(c.status!=='Needs Review'||department==='review'))} onClick={()=>update({department})}>Confirm ownership and assign</button></>}
   {admin&&c.status==='Needs Review'&&<><label>External authority<input maxLength={160} disabled={busy} value={authority} onChange={e=>setAuthority(e.target.value)} placeholder="For example: PWD, with verified contact guidance in the note"/></label><button className="secondary full" disabled={blocked||authority.trim().length<3} onClick={()=>update({action:'refer',authority})}>Record external referral guidance</button></>}
  </div>}
  <p className="footnote">JanSamadhan is an independent civic reporting service. Updates record actions by authorized accounts; they do not establish government affiliation.</p>
 </section></div>;
}
