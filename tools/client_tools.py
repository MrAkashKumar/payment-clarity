from core.data import STORE

def get_client_profile(client_id: str) -> dict:
    row = STORE.clients.get(client_id)
    return dict(row) if row else {'error': 'Client not found', 'client_id': client_id}

def get_clients_by_country(country: str) -> list[dict]:
    return [dict(r) for r in STORE.clients.values() if r['country'] == country]
