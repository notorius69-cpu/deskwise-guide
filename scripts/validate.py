from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re
ROOT=Path(__file__).resolve().parents[1]/'dist'
class Parse(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=[];self.h1=0;self.title=False;self.desc=False;self.canonical=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='h1':self.h1+=1
  if tag=='title':self.title=True
  if a.get('name')=='description':self.desc=True
  if a.get('rel')=='canonical':self.canonical=True
  if 'id' in a:self.ids.append(a['id'])
  for k in ['href','src']:
   if k in a:self.links.append(a[k])
files=list(ROOT.rglob('*.html'));assert len(files)==18,len(files)
errors=[];tags=0
for f in files:
 s=f.read_text();p=Parse();p.feed(s)
 if p.h1!=1 or not all([p.title,p.desc,p.canonical]):errors.append(f'{f}: invalid metadata/headings')
 if len(p.ids)!=len(set(p.ids)):errors.append(f'{f}: duplicate IDs')
 for j in re.findall(r'<script type="application/ld\+json">(.*?)</script>',s):json.loads(j)
 for link in p.links:
  u=urlsplit(link)
  if u.scheme or u.netloc:
   if u.netloc in ['www.amazon.com','www.amazon.co.jp']:
    tags+=1
    if 'tag=' in u.query:errors.append(f'{f}: unexpected affiliate tag')
   continue
  dest=(ROOT/u.path.lstrip('/')) if u.path.startswith('/') else f.parent/unquote(u.path)
  if not u.path:dest=f
  if not dest.exists():errors.append(f'{f}: missing {link}')
  if u.fragment and dest.suffix=='.html' and not re.search(r'id=[\"\x27]'+re.escape(u.fragment)+r'[\"\x27]',dest.read_text()):errors.append(f'{f}: missing anchor {link}')
 if 'Contact details will be added' in s or 'draft for launch' in s:errors.append(f'{f}: launch placeholder')
assert tags==24,tags
assert not errors,'\n'.join(errors)
print(f'PASS: {len(files)} HTML pages; all internal links/anchors, unique headings/IDs, structured data and metadata; {tags} untagged Amazon links.')
