import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from ml.clip_features import CivicEncoder
from PIL import Image
import numpy as np
from scipy.special import softmax
encoder=CivicEncoder(device='cpu')
with Image.open(ROOT/'tests/fixtures/external-pothole.jpg') as im:features=encoder.image_features([im.convert('RGB')])
np.save(ROOT/'data/image-v6-clip-run/external_features.npy',features)
p=softmax(100*features@np.load(ROOT/'data/image-v6-clip-run/text_features.npy').T,axis=1)[0]
print(json.dumps(dict(zip(encoder.labels,p.tolist())),indent=2))
