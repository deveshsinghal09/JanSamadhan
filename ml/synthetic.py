"""Reproducible synthetic benchmark. Split by phrase family BEFORE generating rows."""
import csv, json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {
 'Garbage': ['garbage has not been collected','rubbish is piled beside the road','waste collection truck has not arrived','dustbin is overflowing with refuse','street sweeping has been missed','kachra nahi uthaya gaya hai','कूड़ा नहीं उठाया गया है','household trash is lying outside','garbage bags cover the pavement','sanitation workers have missed waste pickup','kachre ka dher laga hai','कचरा सड़क पर पड़ा है'],
 'Road Damage': ['pothole on the municipal road','road surface has broken apart','large cracks in the street','asphalt has washed away','damaged road needs repair','sadak par gaddha hai','सड़क पर गड्ढा है','deep hole in the roadway','uneven broken pavement on local road','potholes make cycling difficult','sadak toot gayi hai','सड़क की मरम्मत चाहिए'],
 'Streetlight': ['streetlight is not working','public lamp flickers all night','street lighting pole lamp is broken','streetlight stays off after sunset','road lamp needs replacement','street light band hai','स्ट्रीट लाइट बंद है','public lighting is out','streetlight bulb has fused','street lamps leave the lane dark','gali ki light nahi jalti','गली की बत्ती नहीं जलती'],
 'Water Supply': ['water supply has stopped','water pipeline is leaking','tap water pressure is very low','drinking water looks dirty','municipal water pipe has burst','pani ki supply band hai','पानी की सप्लाई बंद है','no water reaches our taps','water main leaks continuously','tap water has a foul smell','nal mein ganda pani aa raha hai','नल में गंदा पानी आ रहा है'],
 'Sewerage': ['sewer line is blocked','sewage is overflowing from manhole','sewer cover is missing','underground sewer pipe is clogged','sewage is backing up into houses','sewer ka pani bahar aa raha hai','सीवर का पानी बाहर आ रहा है','manhole is overflowing with sewage','sewerage network needs cleaning','sewer chamber has collapsed','sewer line jam hai','सीवर लाइन जाम है'],
 'Other': ['property tax bill is incorrect','household electricity supply has failed','passport application is delayed','police complaint needs attention','national highway requires repairs','bijli ka bill galat hai','बिजली का बिल गलत है','my pension has not arrived','private apartment lift is broken','land ownership dispute needs help','ration card nahi mila','राशन कार्ड नहीं मिला']
}
SEVERITY = {
 'Low':['minor inconvenience with no immediate danger','routine maintenance requested','small issue and access remains open','halki dikkat hai','सामान्य रखरखाव चाहिए','please schedule a routine inspection'],
 'Medium':['affecting several households for two days','repeated problem disrupting daily use','residents have difficulty using this lane','do din se pareshani hai','दो दिन से परेशानी है','daily activities are being disrupted'],
 'High':['someone is injured and needs urgent help','exposed live wire creates an electrocution risk','contamination is making children sick','ambulance access is blocked','तुरंत खतरा है लोग घायल हैं','immediate danger to residents']
}

def generate():
 rng=random.Random(42)
 places=json.loads((ROOT/'data/directory.json').read_text(encoding='utf8'))['localities']
 rows=[]
 # 8 training, 2 validation and 2 test families in each category; no family crosses splits.
 for category, phrases in FAMILIES.items():
  for family, phrase in enumerate(phrases):
   split='train' if family<8 else 'validation' if family<10 else 'test'
   for urgency, contexts in SEVERITY.items():
    context_ids=range(4) if split=='train' else [4] if split=='validation' else [5]
    for context_id in context_ids:
     for place in places:
      rows.append({'id':f'SYN-{len(rows)+1:05}', 'text':f"{phrase.capitalize()} near {place['name']}; {contexts[context_id]}.", 'category':category,'urgency':urgency,'locality':place['name'],'lat':round(place['lat']+rng.uniform(-.002,.002),6),'lng':round(place['lng']+rng.uniform(-.002,.002),6),'family':f'{category}-{family}','split':split,'is_synthetic':True})
 with (ROOT/'data/synthetic_complaints.csv').open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=rows[0]);writer.writeheader();writer.writerows(rows)
 return rows
