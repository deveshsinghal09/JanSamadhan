const fs=require('node:fs');
(async()=>{
 const root='http://127.0.0.1:3001/api';
 const login=await fetch(root+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:'citizen@demo.in',password:'Review@123'})});const cookie=login.headers.get('set-cookie').split(';')[0];
 const form=new FormData();Object.entries({description:'There is a deep pothole and broken asphalt in the municipal road. Please repair the damaged road.',locality:'Hazratganj',lat:26.8467,lng:80.9462}).forEach(([k,v])=>form.append(k,v));form.append('image',new Blob([fs.readFileSync('tests/fixtures/external-pothole.jpg')],{type:'image/jpeg'}),'pothole.jpg');
 const r=await fetch(root+'/predict',{method:'POST',headers:{Cookie:cookie},body:form});const result=await r.json();
 if(!r.ok)throw Error(JSON.stringify(result));
 fs.writeFileSync('data/external-pothole-evaluation.json',JSON.stringify({purpose:'User-provided external regression image, excluded from training. Lucknow coordinates are preview inputs only, not a claim about the photograph location. No complaint submitted.',expectedVisualIssue:'Pothole / broken asphalt',prediction:result.prediction,imagePrediction:result.imagePrediction},null,2));
 console.log(JSON.stringify({category:result.prediction.category,manualReview:result.prediction.manualReview,evidence:result.prediction.evidence},null,2));
})().catch(e=>{console.error(e.message);process.exitCode=1});
