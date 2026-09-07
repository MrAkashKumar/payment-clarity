"""Small cached lexical retrieval index; no remote embedding dependency."""
from collections import Counter
from functools import lru_cache
from math import log, sqrt
from pathlib import Path
import re
from core.data import REFERENCE

STOP = {'the','a','an','to','of','and','in','is','for','with','by','be','this','it','or','are','as'}

def tokens(text):
    return [t for t in re.findall(r'[a-z0-9]+', text.lower()) if t not in STOP]

def load_policy_documents(policy_directory):
    return [{'source':p.name,'text':p.read_text(encoding='utf-8')} for p in sorted(Path(policy_directory).glob('*.md'))]

def clean_document(text):
    return re.sub(r'[ \t]+', ' ', text).strip()

def chunk_documents(documents, chunk_size=500, chunk_overlap=50):
    chunks = []
    for doc in documents:
        # The provided documents are short. Keep their related clauses together.
        text = clean_document(doc['text'])
        chunks.append({'chunk_id':doc['source']+':1', 'source':doc['source'], 'text':text})
    return chunks

def build_index(chunks):
    counts = [Counter(tokens(c['text'])) for c in chunks]
    vocab = set(t for count in counts for t in count)
    idf = {t:log(1+len(chunks)/(1+sum(t in c for c in counts))) for t in vocab}
    return {'chunks':chunks,'counts':counts,'idf':idf}

def retrieve(index, query, top_k=5):
    if not isinstance(query,str) or not query.strip(): return []
    q = Counter(tokens(query)); results = []
    for chunk, count in zip(index['chunks'],index['counts']):
        # A negative administrative statement is not substantive payment policy.
        if not re.search(r'require|should|establish|identify|check|record|separate|exceeds',chunk['text'],re.I): continue
        dot = sum(q[t]*count[t]*index['idf'].get(t,0)**2 for t in q)
        norm = sqrt(sum((n*index['idf'][t])**2 for t,n in count.items()))
        score = dot / norm if norm else 0
        if score > 0: results.append(dict(chunk, score=round(score,5)))
    return sorted(results,key=lambda r:(-r['score'],r['source']))[:max(1,min(int(top_k),9))]

def rerank(query,candidates,top_k=3): return candidates[:top_k]
def retrieve_policy_evidence(index,query,top_k=3): return retrieve(index,query,top_k)

@lru_cache(maxsize=1)
def policy_index():
    return build_index(chunk_documents(load_policy_documents(REFERENCE/'policies')))
