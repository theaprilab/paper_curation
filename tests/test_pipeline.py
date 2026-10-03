import copy
import unittest
from curator.pipeline import judge, curate, parse_feed
G={'id':'test','topic':'Active Learning','guru':'A Researcher','group':'Lab','guru_type':'main','aliases':['A Researcher'],'members':[]}
def paper(id='1',date='2025-01-01',abstract='Active learning for robot control.'):
 return {'id':id,'date':date,'title':'Research','abstract':abstract,'authors':['A Researcher'],'link':'https://arxiv.org/abs/1','source':'arXiv'}
def snap(papers):return {'papers':papers,'fetched_at':'2026-09-28T00:00:00Z'}
class SelectionTests(unittest.TestCase):
 def test_skip_newer_irrelevant(self):
  p,a=curate(G,snap([paper('new','2025-06-01','Active learning of language models.'),paper()]),{})
  self.assertEqual(p['id'],'1');self.assertIn('robotics_not_matched',a[0]['reasons'])
 def test_topic_required(self):self.assertFalse(judge(paper(abstract='Robotic manipulation.'),G,{})['eligible'])
 def test_wrong_author(self):
  p=paper();p['authors']=['Different Researcher'];self.assertFalse(judge(p,G,{})['eligible'])
 def test_original_date_not_revision(self):
  older=paper('old','2023-01-01');older['updated']='2026-01-01'
  self.assertEqual(curate(G,snap([older,paper()]),{})[0]['id'],'1')
 def test_future(self):self.assertIn('future_date',judge(paper(date='2099-01-01'),G,{})['reasons'])
 def test_review_exclusion(self):self.assertIsNone(curate(G,snap([paper()]),{'test:1':{'decision':'exclude'}})[0])
 def test_review_cannot_override_author(self):
  p=paper();p['authors']=['Someone Else'];self.assertFalse(judge(p,G,{'test:1':{'decision':'include','evidence':'checked','source_url':'https://example.org'}})['eligible'])
 def test_group_requires_evidence_and_dates(self):
  g=copy.deepcopy(G);g['members']=[{'name':'Student','evidence_url':'https://example.org','from':'2020-01-01','to':'2024-12-31'}];p=paper();p['authors']=['Student'];self.assertFalse(judge(p,g,{})['eligible']);p['date']='2024-01-01';self.assertTrue(judge(p,g,{})['eligible'])
 def test_api_error(self):
  with self.assertRaises(ValueError):parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Error</title></entry></feed>')
 def test_word_boundaries(self):self.assertFalse(judge(paper(abstract='Active learning for neurobotanical systems.'),G,{})['eligible'])

class FailureTests(unittest.TestCase):
 def test_partial_failure_retains_previous_without_freshness_reset(self):
  import json, tempfile
  from pathlib import Path
  from unittest.mock import patch
  import curator.pipeline as pipeline
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'config').mkdir();(root/'docs/data').mkdir(parents=True)
   (root/'config/gurus.json').write_text(json.dumps([G]));(root/'config/reviews.json').write_text('{}')
   previous={'slots':[{'id':'test','paper':paper(),'checked_at':'2025-01-01','coverage':{'scanned':1}}]}
   (root/'docs/data/papers.json').write_text(json.dumps(previous))
   with patch.object(pipeline,'ROOT',root),patch.object(pipeline,'collect',side_effect=OSError('offline')):
    result=pipeline.run()
   slot=result['slots'][0]
   self.assertEqual(slot['status'],'source_error');self.assertTrue(slot['retained_previous'])
   self.assertEqual(slot['checked_at'],'2025-01-01');self.assertEqual(slot['paper']['id'],'1')
 def test_no_match_has_no_fabricated_paper(self):
  self.assertIsNone(curate(G,snap([paper(abstract='Active learning for text classification.')]),{})[0])

if __name__=='__main__':unittest.main()
