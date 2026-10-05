const reject = (status, message) => { throw Object.assign(new Error(message), {status}); };

export function canAccess(user, complaint) {
  return user.role === 'admin' || (user.role === 'citizen' && complaint.userId === user.id)
    || (user.role === 'officer' && complaint.department === user.department);
}

export function applyAction(c, user, body, directory) {
  if (!canAccess(user, c)) reject(404, 'Complaint not found');
  if (body.expectedUpdatedAt && body.expectedUpdatedAt !== c.updatedAt)
    reject(409, 'This report has changed. Refresh it before recording your action.');
  let {status, note, department, urgency, action} = body;
  if (typeof note !== 'string' || note.trim().length < 5 || note.length > 1000)
    reject(400, 'Add a 5–1000 character explanation visible to the citizen');
  if ([status, department, urgency, action].filter(v => v !== undefined).length !== 1)
    reject(400, 'Record one action at a time');
  note = note.trim();
  const before = {status:c.status, department:c.department, urgency:c.urgency};
  if (user.role === 'citizen') {
    if (action !== 'request-review' || c.status !== 'Resolved') reject(403, 'Citizens can request review of their resolved reports');
    c.previousDepartment = c.department;
    c.department = 'review'; c.status = 'Needs Review'; c.resolutionDisputed = true;
    note = 'Citizen reports that the issue remains unresolved: ' + note;
  } else if (department !== undefined) {
    if (user.role !== 'admin') reject(403, 'Only an administrator can assign departments');
    const d = directory.departments.find(d => d.id === department);
    if (!d) reject(400, 'Unknown department');
    if (c.status === 'Resolved' || c.status === 'Referred') reject(400, 'Reopen the report before changing its department');
    if (department === c.department && c.status !== 'Needs Review') reject(400, 'Report is already assigned to this department');
    c.department = d.id;
    if (d.id !== 'review') c.category = d.category;
    c.status = d.id === 'review' ? 'Needs Review' : 'Assigned';
    c.resolutionDisputed = false;
    c.routingReview = {by:user.id, at:new Date().toISOString(), note};
    note = `Routing changed from ${before.department} to ${d.id}: ${note}`;
  } else if (urgency !== undefined) {
    if (!['admin','officer'].includes(user.role)) reject(403, 'Staff access required');
    if (!['Low','Medium','High'].includes(urgency)) reject(400, 'Unknown priority');
    if (urgency === c.urgency) reject(400, 'Priority is unchanged');
    if (['Resolved','Referred'].includes(c.status)) reject(400, 'Reopen the report before changing its priority');
    c.urgency = urgency;
    note = `Priority changed from ${before.urgency} to ${urgency}: ${note}`;
  } else if (action === 'request-review') {
    if (!['admin','officer'].includes(user.role) || !['Assigned','In Progress'].includes(c.status))
      reject(400, 'Only active assignments can be returned for review');
    c.previousDepartment = c.department; c.department = 'review'; c.status = 'Needs Review';
    note = 'Returned for administrator review: ' + note;
  } else if (action === 'refer') {
    if (user.role !== 'admin' || c.status !== 'Needs Review') reject(403, 'Administrator review is required for an external referral');
    const authority = typeof body.authority === 'string' ? body.authority.trim() : '';
    if (authority.length < 3 || authority.length > 160) reject(400, 'Specify the responsible external authority');
    c.status = 'Referred'; c.referral = {authority, instructions:note};
    note = `Referral guidance: ${authority}. ${note}. No external submission was sent automatically.`;
  } else if (action === 'note') {
    if (!['admin','officer'].includes(user.role)) reject(403, 'Staff access required');
  } else if (status !== undefined) {
    if (!['admin','officer'].includes(user.role)) reject(403, 'Staff access required');
    const transitions = {'Assigned':['In Progress'], 'In Progress':['Resolved']};
    if (user.role === 'admin' && ['Resolved','Referred'].includes(c.status)) {
      if (status !== 'Needs Review' && !(status === 'In Progress' && c.department !== 'review')) reject(400, 'Reopen for work or administrator review');
      if (status === 'Needs Review') { c.previousDepartment = c.department; c.department = 'review'; }
    } else if (!transitions[c.status]?.includes(status) || c.department === 'review') {
      reject(400, 'Invalid status transition; review cases must be assigned first');
    }
    c.status = status;
    if (status === 'Resolved') c.resolution = {note, at:new Date().toISOString(), by:user.id};
  } else reject(400, 'Unknown action');
  c.updatedAt = new Date(Math.max(Date.now(), Date.parse(c.updatedAt) + 1)).toISOString();
  c.history.push({status:c.status, at:c.updatedAt, note, actor:user.name, actorId:user.id, actorRole:user.role, before, after:{status:c.status,department:c.department,urgency:c.urgency}});
  return c;
}
