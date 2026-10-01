// Decision-level fusion. Raw model scores are preserved, never relabelled as probabilities.
export function combineEvidence(text,photo){
 const result={...text,decisionMethod:photo?'text-image-consensus-v1':'text-only',evidence:{textCategory:text.category,textScore:text.categoryConfidence,photoLabel:photo?.label??null,photoScore:photo?.confidence??null}};
 if(!photo)return result;
 const mapped={'Garbage / litter':'Garbage','Pothole':'Road Damage','Road surface issue':'Road Damage'}[photo.label];
 const floodConflict=photo.label==='Waterlogging / flooded road'&&text.category==='Road Damage'&&photo.confidence>=.7;
 const conflict=floodConflict||(mapped&&mapped!==text.category&&photo.confidence>=.7);
 if(text.manualReview){result.evidence.status='jurisdiction-review';result.evidence.explanation='Text requires ownership or category review. A photo cannot clear that requirement.';}
 else if(conflict){result.manualReview=true;result.evidence.status='conflict';result.evidence.explanation=`Your description suggests ${text.category}; the photo model suggests ${photo.label}. Keep the described category and ask an officer to verify both.`;}
 else if(mapped===text.category&&!photo.manualReview){result.evidence.status='agreement';result.evidence.explanation='The description and accepted photo prediction support the same category.';}
 else{result.evidence.status='photo-inconclusive';result.evidence.explanation='The photo does not provide a reliable category confirmation. The description supplies the proposed category.';}
 result.reason=`${text.reason}. ${result.evidence.explanation}`;
 return result;
}
