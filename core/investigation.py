"""Evidence-backed exercise rule engine. Thresholds are not production policy."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import re
from core.data import STORE
from tools.payment_tools import get_payment,get_client_payments,aggregate_beneficiary_24h
from tools.client_tools import get_client_profile
from tools.policy_tools import search_policy

COUNTRIES={'UAE':'AE','Singapore':'SG','Switzerland':'CH','Hong Kong':'HK','UK':'GB'}
GLOBAL='global_payment_policy.md';SG='regional_singapore.md';CH='regional_switzerland.md';DEST='high_risk_jurisdictions.md';PROC='investigation_procedure.md'

def money(value,currency): return currency+' '+format(Decimal(value),',.2f')

def investigate(payment_id,question='What review is required?'):
    trace=[]
    def call(name,func,**kwargs):
        result=func(**kwargs);trace.append({'tool':name,'arguments':kwargs});return result
    payment=call('get_payment',get_payment,payment_id=payment_id)
    if 'error' in payment: raise KeyError('Payment not found')
    client=call('get_client_profile',get_client_profile,client_id=payment['client_id'])
    if 'error' in client: raise ValueError('Client information unavailable')
    history=call('get_client_payments',get_client_payments,client_id=payment['client_id'])
    grouped=call('aggregate_beneficiary_24h',aggregate_beneficiary_24h,client_id=payment['client_id'],beneficiary_name=payment['beneficiary_name'])
    queries=['Global payment monitoring USD 100000 equivalent same client beneficiary structuring',
             'High risk jurisdiction AE additional review', 'Investigation procedure establish facts assumptions record evidence']
    if client['country'] in ('Singapore','Switzerland'): queries.append(client['country']+' payment procedure thresholds RM enhanced review')
    evidence={}
    for query in queries:
        for hit in call('search_policy',search_policy,query=query,top_k=3): evidence[hit['source']]=hit
    checks=[]; assumptions=[]; missing=[]
    def add(check_id,title,triggered,detail,source,clause,requirement=None,calculation=None):
        doc=evidence.get(source)
        supported=doc and re.sub(r'\s+',' ',clause).lower() in re.sub(r'\s+',' ',doc['text']).lower()
        checks.append({'id':check_id,'title':title,'triggered':bool(triggered) if supported else None,
            'state':'complete' if supported else 'needs_information','detail':detail if supported else 'Applicable policy evidence is unavailable or changed; review the rule mapping.',
            'source':source,'clause':clause,'requirement':requirement if triggered and supported else None,'calculation':calculation})
        if not supported: missing.append('Confirm current policy mapping for '+source)
    amount=Decimal(payment['amount']);currency=payment['currency'];region=client['country']
    def comparison(value,threshold,threshold_currency):
        if currency!=threshold_currency:
            note=f'Exercise-only 1:1 equivalence: {currency} to {threshold_currency}; approved FX is not supplied.'
            if note not in assumptions:assumptions.append(note)
        return {'value':str(value),'value_currency':currency,'operator':'>','threshold':str(threshold),'threshold_currency':threshold_currency,'basis':'native currency' if currency==threshold_currency else 'exercise 1:1 equivalence'}
    calc=comparison(amount,100000,'USD')
    add('global_amount','Global enhanced-review amount check',amount>100000,
        money(amount,currency)+(' exceeds ' if amount>100000 else ' does not exceed ')+'USD 100,000 equivalent.',GLOBAL,
        'Payments above USD 100,000 equivalent require enhanced review before release.','Enhanced review',calc)
    if region=='Singapore':
        for cid,limit,label,clause in [('regional_rm',75000,'RM review','Payments above USD 75,000 equivalent require RM review.'),('regional_enhanced',100000,'Enhanced review','Payments above USD 100,000 equivalent require enhanced review.')]:
            add(cid,'Singapore '+label,amount>limit,money(amount,currency)+(' exceeds ' if amount>limit else ' does not exceed ')+f'USD {limit:,} equivalent.',SG,clause,label,comparison(amount,limit,'USD'))
    elif region=='Switzerland':
        for cid,limit,label,clause in [('regional_rm',80000,'RM review','Payments above CHF 80,000 equivalent require RM review.'),('regional_enhanced',120000,'Enhanced review','Payments above CHF 120,000 equivalent require enhanced review.')]:
            add(cid,'Switzerland '+label,amount>limit,money(amount,currency)+(' exceeds ' if amount>limit else ' does not exceed ')+f'CHF {limit:,} equivalent.',CH,clause,label,comparison(amount,limit,'CHF'))
    code=payment['beneficiary_country_code']
    add('destination','Destination review',code=='AE',f'Authoritative destination code: {code}. The supplied exercise list identifies AE.',DEST,'Payments to AE require additional review.','Additional destination review')
    group=next(g for g in grouped['groups'] if g['date']==payment['payment_date'] and g['currency']==currency)
    total=Decimal(group['total_amount']); pattern=group['count']>1 and total>100000
    assumptions.append('Same calendar date is used as the 24-hour window because exact timestamps are not supplied.')
    add('pattern','Related-payment pattern',pattern,f"{group['count']} matching payment(s) on {group['date']} total {money(total,currency)}. Filter: same client, beneficiary, date, and currency.",GLOBAL,
        'Multiple payments to the same beneficiary by the same client within 24 hours should be reviewed for potential structuring if their combined value exceeds USD 100,000 equivalent.',
        'Potential structuring review',comparison(total,100000,'USD'))
    if region=='Switzerland' and pattern:
        add('escalation','Swiss escalation requirement',True,'The observed pattern requires Compliance escalation under the supplied Swiss procedure. Intent is not established.',CH,'Potential structuring should be escalated to Compliance.','Compliance escalation')
    other_groups=[g for g in grouped['groups'] if g['date']==payment['payment_date'] and g['currency']!=currency]
    if other_groups:
        missing.append('Approved FX for same-day, same-beneficiary payments in other currencies; combined cross-currency assessment is incomplete.')
    mismatch=COUNTRIES.get(payment['beneficiary_country'])!=code
    discrepancy={'label':payment['beneficiary_country'],'code':code,'message':f"Country label says {payment['beneficiary_country']}; code says {code}. The code is authoritative for this exercise."} if mismatch else None
    requirements=list(dict.fromkeys(c['requirement'] for c in checks if c['requirement']))
    request_items=[]
    if requirements:
        request_items=['Payment purpose','Supporting invoice or agreement','Relationship with the beneficiary']
        if mismatch:request_items.append('Confirmation of intended destination')
        if pattern:request_items+=['Reason for separate transfers','Actual payment timestamps']
    if mismatch:missing.append('Resolve the destination label/code discrepancy under the appropriate procedure.')
    if pattern:missing.append('Confirm the commercial purpose and relationship of the related transfers; intent is unknown.')
    # Verify procedure evidence without implying the investigation itself is a release approval.
    add('procedure','Investigation procedure evidence',False,'Facts, policies, destination, pattern, assumptions, and supporting evidence have been assembled for review.',PROC,'Record the evidence supporting the recommendation.')
    unknown=any(c['state']!='complete' for c in checks) or bool(other_groups)
    if unknown:title='Investigation needs more evidence'
    elif pattern:title='Related payments require pattern review'
    elif 'Enhanced review' in requirements:title='Enhanced review'+(' + destination review' if code=='AE' else ' required')
    elif 'RM review' in requirements:title='RM review'+(' + destination review' if code=='AE' else ' required')
    elif code=='AE':title='Additional destination review required'
    else:title='No review trigger established by these checks'
    if requirements:
        if pattern: draft=f"For your payments to {payment['beneficiary_name']} on {payment['payment_date']}, please provide the purpose and supporting documents for each transfer, and confirm why they were made separately."
        else:draft=f"For payment {payment_id} to {payment['beneficiary_name']}, please confirm the payment purpose and your relationship with the beneficiary. Please provide a supporting invoice or agreement, if available."
        if mismatch:draft+=' Please also confirm the intended destination.'
    else:draft='Internal analyst note: inspect the completed checks, resolve any data discrepancies, and follow the remaining bank review procedure. These checks do not authorise payment release.'
    citations=sorted({c['source'] for c in checks if c['source'] in evidence})
    lines=[title+'.']+[c['title']+': '+c['detail'] for c in checks]
    if discrepancy:lines.append(discrepancy['message'])
    lines+=['Assumptions: '+' '.join(assumptions),'A policy trigger does not establish suspicious activity. No payment release is authorised.']
    if request_items:lines.append('Proposed information request: '+', '.join(request_items)+'.')
    lines.append('Workflow: establish facts, identify applicable policy, check destination and related transfers, separate facts from assumptions, and record evidence for human review.')
    return {'payment_id':payment_id,'question':question,'title':title,'payment':payment,'client':client,'checks':checks,
        'requirements':requirements,'evidence':[evidence[k] for k in citations], 'citations':citations,
        'facts':dict(payment,client_country=region,related_payment_ids=group['payment_ids'],related_count=group['count'],related_total=group['total_amount'],related_currency=currency),
        'related_group':group,'other_currency_groups':other_groups,'history_count':len(history),'discrepancy':discrepancy,'assumptions':assumptions,
        'missing_information':missing,'request_items':request_items,'draft':draft,'external_request_needed':bool(requirements),
        'status':'incomplete' if unknown else 'ready_for_review','answer':'\n\n'.join(lines),'tools_used':list(dict.fromkeys(t['tool'] for t in trace)),
        'trace':trace,'input_version':STORE.version,'mode':'deterministic','mode_label':'Evidence mode · no live AI',
        'generated_at':datetime.now(timezone.utc).isoformat(),'guardrails':['Exercise policies only','Human review required','No payment actions'],
        'limitation':'The deterministic evidence engine is running. The required live LLM agent is not enabled.'}
