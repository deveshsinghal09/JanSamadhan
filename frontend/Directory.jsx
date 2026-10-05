import React from 'react';
import {Building2,ArrowUpRight} from 'lucide-react';
import './directory.css';

export default function DepartmentDirectory({directory}){
 const contact=directory.contact;
 return <>
  <div className="page-heading"><div><p className="eyebrow">WHO HANDLES WHAT</p><h1>A department. A responsible role.</h1><p>Find the suggested desk and open its contact guidance below.</p></div></div>
  <div className="contact-strip"><Building2 size={30}/><div><h2>Start with the LMC control room</h2><p><a href={`tel:${contact.phone}`}>{contact.phone}</a> · <a href={`mailto:${contact.email}`}>{contact.email}</a></p><small>{contact.address}</small></div><a className="secondary" target="_blank" rel="noreferrer" href={contact.source}>Official contact page <ArrowUpRight size={16}/></a></div>
  <p className="footnote">{directory.disclaimer} General LMC contact details checked on 9 September 2026. No call or email is sent by viewing these details.</p>
  <div className="directory-list">{directory.departments.map(d=>{
   const referral=['water','sewer'].includes(d.id);
   const historical=d.source.endsWith('.pdf');
   return <article key={d.id}><span className="department-code">{d.id.slice(0,3).toUpperCase()}</span><div>
    <h2>{d.name}</h2><p className="officer-role">{d.officer}</p><p>{d.scope}</p><small>Proposed escalation: {d.escalation}</small>
    <details className="department-contacts"><summary>View contacts — {d.category}</summary>
     <div className="department-contact-body">
      <p><strong>{referral?'Referral contact: LMC control room':'General contact: LMC control room'}</strong></p>
      <p>{referral?'A working direct Jal Kal contact page could not be verified. Ask the LMC control room to confirm the relevant Jal Kal zone and current operator; the numbers below are LMC contacts, not direct Jal Kal officer numbers.':d.id==='review'?'This queue is managed by JanSamadhan administrators. For an external referral, ask the LMC control room which authority handles the issue.':`Ask the control room for the ${d.officer} responsible for your locality.`}</p>
      <p>Phone: <a href={`tel:${contact.phone}`}>{contact.phone}</a></p>
      <p>Calling / WhatsApp numbers: {contact.alternate.split(' / ').map((number,i)=><React.Fragment key={number}>{i>0?' · ':''}<a href={`tel:+91${number}`}>{number}</a></React.Fragment>)}</p>
      <p>Email: <a href={`mailto:${contact.email}`}>{contact.email}</a></p>
      <p>Office: {contact.address}</p>
      <a href={contact.source} target="_blank" rel="noreferrer">Check these details on the official LMC contact page <ArrowUpRight size={15}/></a>
      <p className="footnote">Provide the locality, nearby landmark and issue description. Confirm the current responsible officer before sending a complaint.</p>
     </div>
    </details>
    {historical&&<details className="department-reference"><summary>Background reference — historical document</summary><p className="footnote">{d.note} This document supports the proposed role or responsibility; it is not a verified current contact list.</p><a href={d.source} target="_blank" rel="noreferrer">Open {d.id==='sewer'?'historical sanitation plan':'historical officer directory'} (PDF) <ArrowUpRight size={15}/></a></details>}
   </div></article>;
  })}</div>
 </>;
}
