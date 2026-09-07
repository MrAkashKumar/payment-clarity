import io,json,unittest,urllib.error
from unittest.mock import patch
from agent.agent import run_agent,validate_model_output,NoRedirect
from core.investigation import investigate

class AdapterTests(unittest.TestCase):
 def response(self,message):
  return io.BytesIO(json.dumps({'choices':[{'message':message}]}).encode())
 def test_live_tool_loop(self):
  base=investigate('P50002');requests=[]
  def provider(req,timeout):
   payload=json.loads(req.data);requests.append(payload)
   if len(requests)==1:
    return self.response({'tool_calls':[{'id':'call_one','type':'function','function':{'name':'get_payment','arguments':'{"payment_id":"P50002"}'}}]})
   return self.response({'content':json.dumps({'explanation':'The regional and destination policies require review. Payment release is not authorised.','citations':base['citations']})})
  with patch('agent.agent.configured',return_value=True),patch.dict('os.environ',{'LLM_API_KEY':'test','LLM_MODEL':'test','LLM_CHAT_URL':'https://example.invalid/chat'}),patch('agent.agent.provider_request',side_effect=provider):
   r=run_agent('Explain','P50002')
  self.assertEqual(r['mode'],'live_ai');self.assertEqual(requests[0]['tool_choice'],'required');self.assertEqual(requests[1]['tool_choice'],'auto')
  self.assertFalse(requests[0]['store']);self.assertTrue(requests[0]['response_format']['json_schema']['strict'])
  self.assertTrue(all(t['function']['strict'] for t in requests[0]['tools']))
  self.assertTrue(any(t.get('initiated_by')=='llm' for t in r['trace']))
 def test_invalid_narrative_rewrites_once(self):
  base=investigate('P50002')
  replies=[self.response({'tool_calls':[{'id':'x','type':'function','function':{'name':'get_payment','arguments':'{"payment_id":"P50002"}'}}]}),self.response({'content':json.dumps({'explanation':'Review 85000 dollars.','citations':base['citations']})}),self.response({'content':json.dumps({'explanation':'Regional and destination reviews are required. Payment release is not authorised.','citations':base['citations']})})]
  with patch('agent.agent.configured',return_value=True),patch.dict('os.environ',{'LLM_API_KEY':'test','LLM_MODEL':'test','LLM_CHAT_URL':'https://example.invalid/chat'}),patch('agent.agent.provider_request',side_effect=replies) as provider:
   r=run_agent('Explain','P50002');self.assertEqual(r['mode'],'live_ai');self.assertEqual(provider.call_count,3)
 def test_untriggered_pattern_and_threshold_order_rejected(self):
  base=investigate('P50002')
  for text in ['This related-payment pattern warrants scrutiny.','The regional threshold is lower than the global threshold.','Enhanced review is required.','This threshold applies.']:
   with self.subTest(text=text),self.assertRaises(ValueError):validate_model_output({'explanation':text,'citations':base['citations']},base)
 def test_error_is_sanitised(self):
  for status,code in [(401,'authentication'),(429,'quota_or_rate_limit')]:
   with self.subTest(status=status),patch('agent.agent.configured',return_value=True),patch.dict('os.environ',{'LLM_API_KEY':'secret-test-token','LLM_MODEL':'test','LLM_CHAT_URL':'https://example.invalid/chat'}),patch('agent.agent.provider_request',side_effect=urllib.error.HTTPError('https://example.invalid',status,'secret-test-token',{},io.BytesIO(b'secret-test-token'))):
    r=run_agent('Explain','P50002');self.assertEqual(r['ai_error_code'],code);self.assertNotIn('secret-test-token',json.dumps(r));self.assertEqual(r['mode'],'fallback')
 def test_spelled_quantities_rejected(self):
  r=investigate('P50002')
  with self.assertRaises(ValueError):validate_model_output({'explanation':'Seventy-five thousand dollars.','citations':r['citations']},r)
 def test_cross_case_tool_rejected(self):
  reply=self.response({'tool_calls':[{'id':'x','type':'function','function':{'name':'get_payment','arguments':'{"payment_id":"P50001"}'}}]})
  with patch('agent.agent.configured',return_value=True),patch.dict('os.environ',{'LLM_API_KEY':'test','LLM_MODEL':'test','LLM_CHAT_URL':'https://example.invalid/chat'}),patch('agent.agent.provider_request',return_value=reply):
   r=run_agent('Explain','P50002');self.assertEqual(r['ai_error_reason'],'Cross-case tool access denied')
 def test_redirect_denied(self):
  self.assertIsNone(NoRedirect().redirect_request(None,None,302,'',{},'https://other.invalid'))
