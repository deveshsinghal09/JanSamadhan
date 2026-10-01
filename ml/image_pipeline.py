"""Load the deployed image pipeline and track every model used by it."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'ml/image_pipeline.json'

def configuration():
    return json.loads(CONFIG.read_text()) if CONFIG.exists() else None

def signature():
    config = configuration()
    paths = [ROOT / 'ml/image_model.pt']
    if config:
        paths += [CONFIG, ROOT / config['road_model']]
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in paths)

def load_classifier():
    from ml.vision import ImageClassifier
    config = configuration()
    classifier = ImageClassifier(road_model_path=ROOT / config['road_model'] if config else None)
    if config:
        classifier.version = config['version']
        classifier.class_thresholds.update(config['class_thresholds'])
        classifier.road_acceptance_validated = True
    return classifier
