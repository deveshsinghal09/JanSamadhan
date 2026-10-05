import React,{useEffect,useState} from 'react';
import {api} from './api.js';

function AccountRow({user,directory,onSaved}) {
 const [role,setRole]=useState(user.role),[department,setDepartment]=useState(user.department||directory.departments[0].id),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const changed=role!==user.role||(role==='officer'&&department!==user.department);
 async function save(){setBusy(true);setError('');try{const updated=await api('/admin/users/'+user.id,{method:'PATCH',body:JSON.stringify({role,department})});onSaved(updated)}catch(e){setError(e.message)}finally{setBusy(false)}}
 return <article className="panel account-row"><div><strong>{user.name}</strong><p>{user.email}</p></div>{user.role==='admin'?<span className="badge">Administrator</span>:<><label>Role<select disabled={busy} value={role} onChange={e=>setRole(e.target.value)}><option value="citizen">Citizen</option><option value="officer">Officer</option></select></label>{role==='officer'&&<label>Department<select disabled={busy} value={department} onChange={e=>setDepartment(e.target.value)}>{directory.departments.filter(d=>d.id!=='review').map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></label>}<button className="secondary" disabled={busy||!changed} onClick={save}>{busy?'Saving…':'Save access'}</button></>}{error&&<p role="alert" className="error-text">{error}</p>}</article>;
}
export default function AdminUsers({directory}) {
 const [users,setUsers]=useState([]),[query,setQuery]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(true),[notice,setNotice]=useState('');
 async function load(){setLoading(true);setError('');try{setUsers(await api('/admin/users'))}catch(e){setError(e.message)}finally{setLoading(false)}}
 useEffect(()=>{load()},[]);
 return <><div className="page-heading"><div><p className="eyebrow">ADMINISTRATION</p><h1>People and permissions.</h1><p>Ask officers to create their own account first. Verify their identity, then grant access to the correct department.</p></div><button className="secondary" onClick={load}>Refresh accounts</button></div>
 <p className="alert">Officers can read and update every report in their assigned department. Grant this access only after verifying the person. Citizens can see only their own reports.</p>
 <label>Find an account<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by name or email"/></label>
 {error&&<p role="alert" className="error-text">{error}</p>}{notice&&<p role="status">{notice}</p>}{loading?<p role="status">Loading accounts…</p>:users.filter(u=>(u.name+' '+u.email).toLowerCase().includes(query.toLowerCase())).map(u=><AccountRow key={u.id+u.role+u.department} user={u} directory={directory} onSaved={next=>{setUsers(previous=>previous.map(x=>x.id===next.id?next:x));setNotice('Access updated for '+next.email)}}/>)}
 </>;
}
