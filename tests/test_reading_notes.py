import json
import unittest
from curator.pipeline import ROOT, reading_note

class ReadingNotesTests(unittest.TestCase):
 def test_current_notes_use_actual_abstract_evidence(self):
  data=json.loads((ROOT/'docs/data/papers.json').read_text())
  for slot in data['slots']:
   p=slot.get('paper')
   if not p: continue
   with self.subTest(guru=slot['id']):
    self.assertTrue(p['reading_note']['evidence'])
    for e in p['reading_note']['evidence']:self.assertIn(e,p['abstract'])
 def test_new_paper_extracts_method_and_validation(self):
  p={'abstract':'Robots face uncertainty. We propose a belief model. We evaluate it on a simulated robot.','link':'https://example.org'}
  note=reading_note(p,{})
  self.assertEqual(note['application'],'We propose a belief model.')
  self.assertEqual(note['validation_scope'],'We evaluate it on a simulated robot.')
  self.assertEqual(note['method'],'extractive_abstract')
 def test_changed_abstract_does_not_reuse_invalid_evidence(self):
  p={'abstract':'We propose a new model.','link':'https://example.org'}
  note=reading_note(p,{'reading_note':{'evidence':['Old unsupported claim.']}})
  self.assertEqual(note['method'],'extractive_abstract')
