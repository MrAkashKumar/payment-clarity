import json,os,sys,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core.data import STORE
from core.investigation import investigate
from tools.payment_tools import aggregate_rows,get_payment
from tools.policy_tools import search_policy
from agent.agent import run_agent,validate_model_output

class CoreTests(unittest.TestCase):
 def test_regional_destination(self):
  r=investigate('P50002');self.assertEqual(set(r['requirements']),{'RM review','Additional destination review'});self.assertTrue(r['discrepancy'])
 def test_pattern_membership(self):
  r=investigate('P50003');self.assertEqual(set(r['related_group']['payment_ids']),{'P50003','P50180','P50181'});self.assertEqual(Decimal(r['related_group']['total_amount']),Decimal('110000'));self.assertIn('Compliance escalation',r['requirements']);self.assertTrue(any('1:1' in a for a in r['assumptions']))
 def test_combined(self):
  self.assertEqual(set(investigate('P50001')['requirements']),{'Enhanced review','RM review','Additional destination review'})
 def test_control(self):
  r=investigate('P50000');self.assertEqual(r['requirements'],[]);self.assertFalse(r['external_request_needed']);self.assertIn('No payment release is authorised',r['answer'])
 def test_unknown(self):
  self.assertIn('error',get_payment('missing'))
  with self.assertRaises(KeyError):investigate('missing')
 def test_boundaries(self):
  original=dict(STORE.payments['P50002'])
  for value,requirement,expected in [('75000','RM review',False),('75000.01','RM review',True),('100000','Enhanced review',False),('100000.01','Enhanced review',True)]:
   with self.subTest(value=value),patch.dict(STORE.payments,{'P50002':dict(original,amount=value)}):self.assertEqual(requirement in investigate('P50002')['requirements'],expected)
 def test_group_separates_currency_date(self):
  rows=[dict(STORE.payments['P50003']),dict(STORE.payments['P50180'],currency='USD'),dict(STORE.payments['P50181'],payment_date='2026-04-12')]
  self.assertEqual(len(aggregate_rows(rows,'C2003','Northstar Trading')),3)
 def test_cross_currency_incomplete(self):
  with patch.dict(STORE.payments,{'TEST':dict(STORE.payments['P50003'],payment_id='TEST',currency='USD')}):self.assertEqual(investigate('P50003')['status'],'incomplete')
 def test_no_policy_incomplete(self):
  with patch('core.investigation.search_policy',return_value=[]):
   r=investigate('P50001');self.assertEqual(r['status'],'incomplete');self.assertEqual(r['citations'],[])
 def test_changed_policy_incomplete(self):
  real=search_policy
  def changed(query,top_k=5):return [dict(x,text=x['text'].replace('USD 100,000','USD 900,000')) for x in real(query,top_k)]
  with patch('core.investigation.search_policy',side_effect=changed):self.assertEqual(investigate('P50001')['status'],'incomplete')
 def test_retrieval(self):
  self.assertEqual(search_policy('Singapore RM payment above USD 75000',3)[0]['source'],'regional_singapore.md')
  for query in ['high risk jurisdiction AE','structuring same beneficiary client','investigation procedure']:
   hits=search_policy(query);self.assertTrue(hits);self.assertFalse(any('decoy' in h['source'] for h in hits))
  self.assertEqual(search_policy('zzzznonsense'),[])
 def test_model_guardrails(self):
  r=investigate('P50002')
  for text,citations in [('Needs review.',['unknown.md']),('Pay 999.',r['citations']),('This is approved.',r['citations'])]:
   with self.assertRaises(ValueError):validate_model_output({'explanation':text,'citations':citations},r)
 def test_no_key(self):
  with patch.dict(os.environ,{'LLM_API_KEY':'','LLM_MODEL':'','LLM_CHAT_URL':''}):self.assertEqual(run_agent('What review?','P50002')['mode'],'deterministic')
 def test_provider_failure(self):
  with patch.dict(os.environ,{'LLM_API_KEY':'test','LLM_MODEL':'test','LLM_CHAT_URL':'https://example.invalid/chat'}),patch('agent.agent.provider_request',side_effect=TimeoutError):
   r=run_agent('What review?','P50002');self.assertEqual(r['mode'],'fallback');self.assertEqual(r['facts']['amount'],'85000.0')
 def test_all_184(self):
  for pid in STORE.payments:
   with self.subTest(payment=pid):
    r=investigate(pid);self.assertEqual(r['status'],'ready_for_review');self.assertTrue(r['citations']);self.assertTrue(all(c['state']=='complete' for c in r['checks']));self.assertFalse(any('decoy' in c for c in r['citations']));self.assertEqual(set(r['tools_used']),{t['tool'] for t in r['trace']})
 def test_ten_questions(self):
  qs=json.loads((Path(__file__).resolve().parents[1]/'questions/questions.json').read_text());self.assertEqual(len(qs),10)
  with patch.dict(os.environ,{'LLM_API_KEY':'','LLM_MODEL':'','LLM_CHAT_URL':''}):
   for q in qs:self.assertTrue({'answer','citations','facts','tools_used'}.issubset(run_agent(q['question'],q['payment_id'])))
if __name__=='__main__':unittest.main()
