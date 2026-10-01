"""Download a pinned CLIP research checkpoint; never upload complaint photographs."""
import os
os.environ['HF_HUB_DISABLE_XET']='1'
from pathlib import Path
from huggingface_hub import HfApi,snapshot_download
root=Path(__file__).resolve().parents[1]
repo='openai/clip-vit-base-patch32';revision='3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268'
path=snapshot_download(repo_id=repo,revision=revision,local_dir=root/'data/clip-pretrained',allow_patterns=['config.json','preprocessor_config.json','tokenizer_config.json','tokenizer.json','vocab.json','merges.txt','special_tokens_map.json','pytorch_model.bin'])
(root/'data/clip-pretrained/revision.txt').write_text(revision)
print('Downloaded pinned CLIP:',revision,flush=True)
