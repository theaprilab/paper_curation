import unittest
from curator.pipeline import update_history

def slot(paper_id, status='selected', guru='g'):
 return {'id':guru,'status':status,'publication_url':'https://example.org','paper':{'id':paper_id,'title':paper_id}}

class HistoryTests(unittest.TestCase):
 def test_replacement_and_repeat(self):
  old={'generated_at':'2026-01-01','slots':[slot('a')]}
  records=update_history(old,[slot('b')],'2026-02-01')
  a=next(r for r in records if r['key']=='g:a')
  self.assertEqual(a['archived_at'],'2026-02-01')
  self.assertEqual(a['first_selected_at'],'2026-01-01')
  repeated=update_history({'slots':[slot('b')],'history':records},[slot('b')],'2026-03-01')
  self.assertEqual(len(repeated),2)
  self.assertEqual(next(r for r in repeated if r['key']=='g:a')['archived_at'],'2026-02-01')
 def test_reselection(self):
  records=update_history({'slots':[slot('a')],'generated_at':'2026-01-01'},[slot('b')],'2026-02-01')
  records=update_history({'slots':[slot('b')],'history':records},[slot('a')],'2026-03-01')
  a=next(r for r in records if r['key']=='g:a')
  self.assertIsNone(a['archived_at']);self.assertEqual(a['first_selected_at'],'2026-01-01')
 def test_error_does_not_archive_or_refresh(self):
  records=update_history({'slots':[]},[slot('a')],'2026-01-01')
  records=update_history({'slots':[slot('a')],'history':records},[slot('a','source_error')],'2026-02-01')
  self.assertIsNone(records[0]['archived_at']);self.assertEqual(records[0]['last_selected_at'],'2026-01-01')
 def test_empty_or_removed_slot_archives(self):
  records=update_history({'slots':[slot('a')]},[],'2026-02-01')
  self.assertEqual(records[0]['archived_at'],'2026-02-01')
 def test_same_paper_different_gurus(self):
  records=update_history({'slots':[]},[slot('a',guru='g'),slot('a',guru='h')],'2026-01-01')
  self.assertEqual(len(records),2)
