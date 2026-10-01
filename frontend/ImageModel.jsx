import React,{useEffect,useState} from 'react';

const pct=n=>(100*(n||0)).toFixed(1)+'%';

function LearningCurve({history,best}){

 const x=i=>55+i*510/Math.max(1,history.length-1),y=v=>170-140*v;

 return <figure style={{margin:'18px 0'}}><figcaption>Validation macro F1 by epoch · selected checkpoint: {best}</figcaption><svg viewBox="0 0 610 210" role="img" aria-label="Image model validation macro F1 learning curve" style={{width:'100%',maxWidth:700}}>{[0,.25,.5,.75,1].map(v=><g key={v}><line x1="55" x2="575" y1={y(v)} y2={y(v)} stroke="#dbe6df"/><text x="6" y={y(v)+4} fontSize="11" fill="#52665c">{Math.round(v*100)}%</text></g>)}<polyline fill="none" stroke="#17644b" strokeWidth="3" points={history.map((h,i)=>`${x(i)},${y(h.validation_macro_f1)}`).join(' ')}/>{history.map((h,i)=><g key={h.epoch}><circle cx={x(i)} cy={y(h.validation_macro_f1)} r={h.epoch===best?6:4} fill={h.epoch===best?'#c48b30':'#17644b'}><title>Epoch {h.epoch}: {pct(h.validation_macro_f1)}</title></circle><text x={x(i)} y="194" textAnchor="middle" fontSize="12" fill="#52665c">{h.epoch}</text></g>)}</svg></figure>;

}

export function PhotoPreview({file}){

 const [url,setUrl]=useState('');

 useEffect(()=>{if(!file){setUrl('');return}const next=URL.createObjectURL(file);setUrl(next);return()=>URL.revokeObjectURL(next)},[file]);

 return url?<img className="evidence-image" style={{maxHeight:220,objectFit:'contain'}} src={url} alt="Selected complaint photograph"/>:null;

}

export function ImageResult({result,textCategory}){

 if(!result)return null;
 const disagrees=(textCategory&&result.suggestedCategory&&textCategory!==result.suggestedCategory)||result.agreement?.startsWith('Differs from text');

 return <section className="assigned-box" aria-label="Image analysis result" aria-live="polite"><p className="eyebrow">PHOTO-ONLY EVIDENCE</p><h3>{result.displayLabel||result.label}</h3><p>Model score: <strong>{pct(result.confidence)}</strong> · {result.manualReview?'Manual review recommended':'Visual suggestion'}</p>{result.manualReview&&<p>Possible visual match: {result.label}. Please confirm what is visible in your description.</p>}{result.suggestedCategory&&<p>Photo suggests: {result.suggestedCategory}</p>}{result.agreement&&<p><strong>{result.agreement}</strong></p>}{result.reviewReasons?.map(reason=><p className="footnote" key={reason}>{reason}</p>)}<p className="footnote">{result.note}</p><details><summary>Model details and alternative matches</summary><p>Raw photo-model match: {result.label} · model score {pct(result.confidence)}. This score is not a guarantee of correctness.</p>{Object.entries(result.scores).map(([k,v])=><p key={k}>{k}: {pct(v)}</p>)}<p>{result.method} · {result.modelVersion}</p></details></section>;

}

export default function ImageEvidence(){

 const [m,setM]=useState(null),[error,setError]=useState('');

 useEffect(()=>{const c=new AbortController();fetch('/api/image-metrics',{signal:c.signal}).then(async r=>{const data=await r.json();if(!r.ok)throw Error(data.error);return data}).then(setM).catch(e=>{if(e.name!=='AbortError')setError(e.message)});return()=>c.abort()},[]);

 return <section className="panel explanation"><p className="eyebrow">A SECOND MODEL · IMAGE CLASSIFICATION</p><h2>What can the photograph show?</h2>{error&&<p role="status">{error}</p>}{!m&&!error&&<p>Loading image training evidence…</p>}{m&&<>

  <p>{m.classifierTraining?'CLIP supplies frozen image features. A civic classifier is fitted on the training images; regularization and semantic blending are selected on validation data.':m.pipeline?m.pipeline.description:'The experiment compares classifier-head training on frozen ImageNet features with full MobileNetV3-Small fine-tuning.'}</p>

  <p><strong>{m.classifierTraining?'Deployed classifier:':m.pipeline?'Base checkpoint:':'Deployed checkpoint:'}</strong> {m.classifierTraining?m.architecture:<>{m.best_epoch<=2?'Frozen CNN backbone with a trained classifier head':'Fine-tuned CNN and classifier head'} (epoch {m.best_epoch})</>}.</p><div className="stats">{[['Retained images',m.audit.retained_images.toLocaleString()],['Training images',m.splits.train.toLocaleString()],['Test accuracy',pct(m.test.report.accuracy)],['Test macro F1',pct(m.test.report['macro avg']['f1-score'])]].map(([label,value])=><div className="stat" key={label}><span>{label}</span><strong>{value}</strong></div>)}</div>

  <p>{m.audit.downloaded_image_files.toLocaleString()} source image files · {m.audit.groups.toLocaleString()} retained groups · {m.splits.validation} validation images · {m.splits.test} test images. Augmented versions are not independent photographs.</p>

  <div className="table-wrap"><table><thead><tr><th>Visual class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Test images</th></tr></thead><tbody>{m.test.labels.map(label=>{const r=m.test.report[label];return <tr key={label}><td>{label}</td><td>{pct(r.precision)}</td><td>{pct(r.recall)}</td><td>{pct(r['f1-score'])}</td><td>{r.support}</td></tr>})}</tbody></table></div>

  <p>Equal weight per held-out group: <strong>{pct(m.test_group_report.accuracy)} accuracy</strong>, <strong>{pct(m.test_group_report['macro avg']['f1-score'])} macro F1</strong> across {Math.round(m.test_group_report['macro avg'].support)} groups. {m.group_evaluation}</p>{m.pipeline&&<><p><strong>Deployed pipeline: {m.modelVersion}.</strong> {m.pipeline.evaluation}</p><p>Road specialist: MobileNetV3-Large, selected epoch {m.pipeline.road_best_epoch}. {m.pipeline.road_training}</p><LearningCurve history={m.pipeline.road_history} best={m.pipeline.road_best_epoch}/><p>The following learning curve and epoch table describe the base civic model.</p></>}{m.classifierTraining?<details><summary>Classifier fitting and validation selection</summary><p>The encoder stays frozen. These are classifier settings, not CNN epochs. Selected C: {m.classifierTraining.C}; semantic weight: {m.classifierTraining.semantic_weight}.</p><div className="table-wrap"><table><thead><tr><th>Regularization C</th><th>Semantic weight</th><th>Validation macro F1</th></tr></thead><tbody>{m.trainingTrials.map((trial,i)=><tr key={i}><td>{trial.C}</td><td>{trial.semantic_weight}</td><td>{pct(trial.validation_macro_f1)}</td></tr>)}</tbody></table></div></details>:<><LearningCurve history={m.history} best={m.best_epoch}/><details><summary>Training epochs and model selection</summary><p>Checkpoint selected by validation macro F1: epoch {m.best_epoch}. Test set evaluated after selection.</p><div className="table-wrap"><table><thead><tr><th>Epoch</th><th>Stage</th><th>Training loss</th><th>Validation F1</th></tr></thead><tbody>{m.history.map(h=><tr key={h.epoch}><td>{h.epoch}</td><td>{h.stage}</td><td>{h.train_loss.toFixed(4)}</td><td>{pct(h.validation_macro_f1)}</td></tr>)}</tbody></table></div></details></>}

  <details><summary>Image confusion matrix</summary><p>Rows: actual. Columns: predicted.</p><div className="table-wrap"><table><thead><tr><th>Class</th>{m.test.labels.map(l=><th key={l}>{l}</th>)}</tr></thead><tbody>{m.test.confusion_matrix.map((row,i)=><tr key={i}><th>{m.test.labels[i]}</th>{row.map((v,j)=><td key={j}>{v}</td>)}</tr>)}</tbody></table></div></details>

  <p>{m.audit.split_policy}</p><p>{m.label_audit}</p><div className="alert warning">This model classifies scenes, not every municipal problem. It cannot establish parking legality, water supply failure, sewer blockage, a working streetlight, urgency or exact location. Arbitrary photos can receive confident predictions.</div>

  <p>The final assessment combines text with photo evidence using explicit consensus rules. Conflicts retain the described category and require officer review. Ambiguous predictions and unsupported classes require manual review. Model scores do not guarantee correctness on new photographs.</p>

  {m.calibration&&<p>Base validation-fitted temperature: {m.calibration.temperature.toFixed(2)}.{m.pipeline&&<> Road temperature: {m.pipeline.road_temperature.toFixed(2)}.</>} Accepted suggestions cover {pct(m.selective_test.coverage)} of test photos, with {pct(m.selective_test.precision)} accuracy among accepted suggestions. {m.calibration.policy}</p>}{m.outdoor_litter_evaluation&&<p><strong>Outdoor litter challenge:</strong> old model recall {pct(m.outdoor_litter_evaluation.v1_recall)}, updated recall {pct(m.outdoor_litter_evaluation.v2_recall)} on {m.outdoor_litter_evaluation.images} held-out TACO photos. {m.outdoor_litter_evaluation.note}</p>}{m.sources?<><h3>Photograph sources and labels</h3>{m.sources.map(source=><p key={source.url}><a href={source.url} target="_blank" rel="noreferrer">{source.name}</a> — {source.scope}</p>)}</>:<>{m.outdoor_litter_source&&<p><a href={m.outdoor_litter_source} target="_blank" rel="noreferrer">Outdoor litter source: TACO</a></p>}{m.additional_source&&<p><a href={m.additional_source} target="_blank" rel="noreferrer">Additional source: TrashNet</a></p>}<p><a href={m.source} target="_blank" rel="noreferrer">Original image dataset source</a></p></>}<p className="footnote">{m.limitations}</p>

 </>}</section>;

}

