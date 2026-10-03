"""Dependency-free, auditable arXiv collector. Run: python3 -m curator.pipeline."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ATOM = {'a': 'http://www.w3.org/2005/Atom', 'o': 'http://a9.com/-/spec/opensearch/1.1/'}
TOPICS = {
 'Active Learning': ['active learning', 'active exploration', 'information gain', 'experimental design', 'bayesian optimization', 'preference learning', 'active preference', 'informative exploration'],
 'Active Inference': ['active inference', 'free energy principle', 'free-energy principle', 'expected free energy', 'free energy minimization'],
 'Information Space': ['information space', 'information-space', 'belief space', 'belief-space', 'partially observable', 'pomdp', 'information gathering', 'information-gathering', 'information-feedback', 'sensor-induced', 'sufficient information', 'sufficient robot'],
 'Hyperdimensional Computing': ['hyperdimensional', 'hyper-dimensional', 'vector symbolic', 'vector-symbolic', 'hypervector']}
ROBOT = ['robot', 'robotic', 'robotics', 'robots', 'autonomous driving', 'autonomous navigation', 'autonomous vehicle', 'autonomous vehicles', 'autonomous agent', 'autonomous agents', 'self-driving', 'quadrotor', 'drone', 'exoskeleton', 'mobile manipulation', 'visual place recognition']

def normalized(value):
 return ' '.join(re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()).split())

def hits(text, terms):
 text = normalized(text)
 return [t for t in terms if re.search(r'\b' + re.escape(normalized(t)) + r'\b', text)]

def parse_feed(raw):
 root = ET.fromstring(raw)
 total = root.findtext('o:totalResults', namespaces=ATOM)
 if total is None:
  raise ValueError('arXiv response lacks totalResults (possible API error)')
 papers = []
 for e in root.findall('a:entry', ATOM):
  get = lambda key: ' '.join(e.findtext('a:' + key, default='', namespaces=ATOM).split())
  link = get('id').replace('http://', 'https://')
  if '/abs/' not in link: raise ValueError('Invalid arXiv entry')
  paper_id = re.sub(r'v\d+$', '', link.split('/abs/')[-1])
  papers.append({'id':paper_id, 'title':get('title'), 'authors':[a.text for a in e.findall('a:author/a:name', ATOM)],
   'date':get('published')[:10], 'updated':get('updated')[:10], 'date_type':'arxiv_first_submission',
   'link':'https://arxiv.org/abs/'+paper_id, 'source':'arXiv', 'abstract':get('summary'),
   'categories':[c.get('term') for c in e.findall('a:category', ATOM)]})
 return papers, int(total)

class Client:
 def __init__(self): self.last = 0
 def get(self, url):
  for attempt in range(3):
   time.sleep(max(0, 3.2 - (time.monotonic()-self.last)))
   try:
    self.last = time.monotonic()
    req = urllib.request.Request(url, headers={'User-Agent':'RoboticsResearchRadar/1.0 (arXiv metadata curation)'})
    with urllib.request.urlopen(req, timeout=35) as r: return r.read()
   except Exception:
    if attempt == 2: raise
    time.sleep(2 ** (attempt+1))

def collect(guru, client, max_results):
 names = guru['aliases'] + [m['name'] for m in guru.get('members',[]) if m.get('evidence_url')]
 query = ' OR '.join('au:"' + n + '"' for n in names)
 papers, total, urls = [], None, []
 for start in range(0,max_results,100):
  url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode({'search_query':query,'start':start,'max_results':min(100,max_results-start),'sortBy':'submittedDate','sortOrder':'descending'})
  batch, total = parse_feed(client.get(url)); papers.extend(batch); urls.append(url)
  if len(papers) >= total: break
  if not batch: raise ValueError('Incomplete pagination')
 unique={p['id']:p for p in papers}
 return {'fetched_at':dt.datetime.now(dt.timezone.utc).isoformat(), 'total':total,'papers':list(unique.values()),'urls':urls,'truncated':len(papers)<total}

def judge(paper, guru, reviews):
 authors={normalized(a) for a in paper['authors']}
 personal=bool(authors & {normalized(a) for a in guru['aliases']})
 members=[m for m in guru.get('members',[]) if normalized(m['name']) in authors and m.get('evidence_url') and m.get('from','0000') <= paper['date'] <= m.get('to','9999')]
 text=paper['title']+'. '+paper['abstract']
 topic=hits(text, TOPICS[guru['topic']]); robot=hits(text, ROBOT)
 review=reviews.get(guru['id']+':'+paper['id'], {})
 reasons=[]
 if not personal and not members: reasons.append('author_not_matched')
 if not topic: reasons.append('topic_not_matched')
 if not robot: reasons.append('robotics_not_matched')
 try:
  if dt.date.fromisoformat(paper['date']) > dt.datetime.now(dt.timezone.utc).date(): reasons.append('future_date')
 except ValueError: reasons.append('invalid_date')
 if 'withdrawn' in text.lower(): reasons.append('withdrawn')
 if review.get('decision') == 'exclude': reasons.append('manual_exclusion')
 # A documented human review can resolve keyword false negatives, never ownership/date failures.
 if review.get('decision') == 'include' and review.get('evidence') and review.get('source_url'):
  reasons=[r for r in reasons if r not in ('topic_not_matched','robotics_not_matched')]
 evidence=[s.strip() for s in re.split(r'(?<=[.!?])\s+',text) if hits(s,ROBOT)]
 return {'eligible':not reasons, 'reasons':reasons,'topic_terms':topic,'robotics_terms':robot,
  'evidence':evidence[:3], 'attribution':'guru_author' if personal else 'verified_group_member' if members else None,
  'membership_evidence':[m['evidence_url'] for m in members], 'review':review}

def reading_note(paper, review):
 """Keep source evidence verbatim; never invent applications for unseen papers."""
 if review.get('reading_note'):
  note=review['reading_note']
  if all(e in paper['abstract'] for e in note.get('evidence',[])):
   return note
 sentences=re.split(r'(?<=[.!?])\s+',paper['abstract'])
 method=[s for s in sentences if re.search(r'\b(propose|introduce|present|framework|approach)\b',s,re.I)]
 results=[s for s in sentences if re.search(r'\b(evaluate|experiment|experiments|results|demonstrate|simulation|simulated)\b',s,re.I)]
 evidence=list(dict.fromkeys(method[:1]+results[:2])) or sentences[:1]
 return {'application':' '.join(method[:1]) if method else '초록에서 방법 문장을 자동 추출하지 못했습니다.',
  'validation_scope':' '.join(results[:2]) if results else '초록에서 실험·검증 문장을 자동 추출하지 못했습니다.',
  'evidence':evidence,'method':'extractive_abstract','source_url':paper['link']}

def curate(guru, snapshot, reviews):
 audit=[]; selected=None
 for p in sorted(snapshot['papers'],key=lambda p:(p['date'],p['id']),reverse=True):
  decision=judge(p,guru,reviews)
  audit.append({'id':p['id'],'title':p['title'],'date':p['date'],**decision})
  if decision['eligible'] and selected is None:
   review=decision['review']
   reviewed=bool(review.get('decision')=='include' and review.get('evidence') and review.get('source_url'))
   sentences=re.split(r'(?<=[.!?])\s+',p['abstract'])
   selected={**p,**{k:guru[k] for k in ('topic','guru','group','guru_type')},
    'guru_id':guru['id'], 'robotics_relevance':{'level':'high' if reviewed else 'candidate','method':'human_review' if reviewed else 'keyword_rules_v1','evidence':decision['evidence'],'matched_terms':decision['robotics_terms']},
    'topic_evidence':decision['topic_terms'], 'attribution':decision['attribution'],
    'summary':review.get('summary') or ' '.join(sentences[:2]),'summary_method':review.get('note_method','human') if review.get('summary') else 'extractive_abstract',
    'why_it_matters':reading_note(p,review)['application'],
    'reading_note':reading_note(p,review),
    'review_status':'reviewed' if reviewed else 'needs_review',
    'verified_at':snapshot['fetched_at'], 'freshness':'latest_matching_in_scanned_arxiv_results'}
 return selected,audit

def write_json(path, value):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n'); os.replace(tmp,path)

def update_history(old, slots, now):
 """One retained record per guru/paper, including current selections."""
 records={r['key']:dict(r) for r in old.get('history',[])}
 for slot in old.get('slots',[]):
  p=slot.get('paper')
  if not p: continue
  key=slot['id']+':'+p['id']
  if key not in records:
   records[key]={'key':key,'guru_id':slot['id'],'paper':p,
    'publication_url':slot.get('publication_url',''),
    'first_selected_at':old.get('generated_at',now),
    'last_selected_at':old.get('generated_at',now),'archived_at':None}
 active=set()
 for slot in slots:
  p=slot.get('paper')
  if not p: continue
  key=slot['id']+':'+p['id'];active.add(key)
  record=records.setdefault(key,{'key':key,'guru_id':slot['id'],'first_selected_at':now})
  record.update(paper=p,publication_url=slot.get('publication_url',''),archived_at=None)
  if slot['status']!='source_error': record['last_selected_at']=now
 for key,record in records.items():
  if key not in active and not record.get('archived_at'): record['archived_at']=now
 return sorted(records.values(),key=lambda r:(r['first_selected_at'],r['key']),reverse=True)

def run(offline=False,max_results=300):
 gurus=json.loads((ROOT/'config/gurus.json').read_text()); reviews=json.loads((ROOT/'config/reviews.json').read_text())
 out=ROOT/'docs/data/papers.json'
 old=json.loads(out.read_text()) if out.exists() else {'slots':[]}
 oldslots={s['id']:s for s in old['slots']}
 slots=[]; audits={}; client=Client()
 for g in gurus:
  path=ROOT/'data/raw'/f"{g['id']}.json"
  try:
   snapshot=json.loads(path.read_text()) if offline else collect(g,client,max_results)
   if not offline: write_json(path,snapshot)
   paper,audit=curate(g,snapshot,reviews); audits[g['id']]=audit
   slot={**g,'status':'selected' if paper else 'no_match','paper':paper,'checked_at':snapshot['fetched_at'],
    'coverage':{'source':'arXiv author search','scanned':len(snapshot['papers']),'total':snapshot['total'],'truncated':snapshot['truncated'],'queries':snapshot['urls']}}
  except Exception as e:
   previous=oldslots.get(g['id'],{})
   slot={**g,'status':'source_error','paper':previous.get('paper'),'checked_at':previous.get('checked_at'),'coverage':previous.get('coverage'), 'error':f'{type(e).__name__}: {e}','retained_previous':bool(previous.get('paper'))}
  slots.append(slot)
  print(g['id'], slot['status'], (slot.get('paper') or {}).get('title',''),flush=True)
 now=dt.datetime.now(dt.timezone.utc).isoformat()
 result={'schema_version':2,'history':update_history(old,slots,now),'generated_at':now,'mode':'offline' if offline else 'live','latest_scope':'검색한 arXiv 저자 논문 범위 내 최신 적합 후보. 전체 출판물의 최신성을 보장하지 않습니다.','slots':slots}
 write_json(out,result); write_json(ROOT/'data/audit.json',audits)
 return result

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--offline',action='store_true'); ap.add_argument('--max-results',type=int,default=300); args=ap.parse_args()
 if args.max_results < 1: ap.error('--max-results must be positive')
 result=run(args.offline,args.max_results)
 # Partial outages remain deployable with visible per-slot warnings; total outages fail CI.
 if all(s['status']=='source_error' for s in result['slots']): raise SystemExit(1)
if __name__=='__main__': main()
