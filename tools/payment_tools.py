from collections import defaultdict
from decimal import Decimal
from core.data import STORE

def get_payment(payment_id: str) -> dict:
    row = STORE.payments.get(payment_id)
    return dict(row) if row else {'error': 'Payment not found', 'payment_id': payment_id}

def get_client_payments(client_id: str) -> list[dict]:
    return [dict(r) for r in STORE.payments.values() if r['client_id'] == client_id]

def aggregate_rows(rows, client_id, beneficiary_name):
    groups = defaultdict(list)
    for row in rows:
        if row['client_id'] == client_id and row['beneficiary_name'] == beneficiary_name:
            groups[(row['payment_date'], row['currency'])].append(dict(row))
    return [{'date': key[0], 'currency': key[1], 'count': len(members),
             'total_amount': str(sum(Decimal(r['amount']) for r in members)),
             'payment_ids': [r['payment_id'] for r in members], 'payments': members}
            for key, members in sorted(groups.items())]

def aggregate_beneficiary_24h(client_id: str, beneficiary_name: str) -> dict:
    return {'client_id': client_id, 'beneficiary_name': beneficiary_name,
            'window_basis': 'Same calendar date; exact timestamps are unavailable.',
            'groups': aggregate_rows(STORE.payments.values(), client_id, beneficiary_name)}

def find_repeated_beneficiaries(client_id):
    history = get_client_payments(client_id)
    return [name for name in sorted({r['beneficiary_name'] for r in history})
            if sum(r['beneficiary_name'] == name for r in history) > 1]
