from rag.pipeline import policy_index, retrieve

def search_policy(query: str, top_k: int=5) -> list[dict]:
    return retrieve(policy_index(),query,top_k)

def get_policy_document(source: str) -> dict:
    return next((dict(c) for c in policy_index()['chunks'] if c['source']==source), {'error':'Policy not found'})
