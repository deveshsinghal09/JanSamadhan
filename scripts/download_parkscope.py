"""Follow the publisher's public Google Drive download form."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode
from download_civic_v3 import download

base=Path(__file__).resolve().parents[1]/'data/images/v4-sources'
class Form(HTMLParser):
    def __init__(self):
        super().__init__();self.action=None;self.fields={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='form' and a.get('id')=='download-form':self.action=a['action']
        if tag=='input' and a.get('type')=='hidden':self.fields[a['name']]=a['value']
form=Form();form.feed((base/'parkscope-response.bin').read_text())
assert form.action=='https://drive.usercontent.google.com/download'
download(form.action+'?'+urlencode(form.fields),base/'parkscope.zip')
print('ParkScope archive downloaded',flush=True)
