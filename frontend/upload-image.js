// Resize locally before upload; the server still independently validates every file.
export async function prepareUpload(original){
 if(!['image/jpeg','image/png'].includes(original.type))throw Error('Choose a PNG or JPEG photograph.');
 if(original.size>20*1024*1024)throw Error('Choose a photo smaller than 20 MB.');
 let image;
 try{image=await createImageBitmap(original)}catch{throw Error('This photo could not be opened. Choose a valid PNG or JPEG.');}
 try{
  if(Math.min(image.width,image.height)<32)throw Error('The photo must be at least 32 × 32 pixels.');
  if(original.size<=3*1024*1024&&Math.max(image.width,image.height)<=1600)return {file:original,note:''};
  const scale=Math.min(1,1600/Math.max(image.width,image.height));
  const canvas=document.createElement('canvas');canvas.width=Math.max(32,Math.round(image.width*scale));canvas.height=Math.max(32,Math.round(image.height*scale));
  const context=canvas.getContext('2d');context.fillStyle='white';context.fillRect(0,0,canvas.width,canvas.height);context.drawImage(image,0,0,canvas.width,canvas.height);
  const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.85));
  if(!blob||blob.size>3*1024*1024)throw Error('The photo is still too large. Choose a smaller photograph.');
  return {file:new File([blob],original.name.replace(/\.[^.]+$/,'')+'.jpg',{type:'image/jpeg'}),note:'Photo resized on your device for upload. Your original file is unchanged.'};
 }finally{image.close();}
}
