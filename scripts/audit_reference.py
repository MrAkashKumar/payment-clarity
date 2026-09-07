"""Read-only audit of the supplied synthetic payment data; no policy decisions."""
import csv
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'reference'
payments = list(csv.DictReader((DATA / 'payments.csv').open()))
clients = list(csv.DictReader((DATA / 'clients.csv').open()))
client_ids = {r['client_id'] for r in clients}
name_codes = {'UAE': 'AE', 'Singapore': 'SG', 'Switzerland': 'CH',
              'Hong Kong': 'HK', 'UK': 'GB'}
groups = defaultdict(list)
for row in payments:
    date.fromisoformat(row['payment_date'])
    Decimal(row['amount'])
    groups[(row['client_id'], row['beneficiary_name'], row['payment_date'], row['currency'])].append(row)
repeated = [dict(client_id=k[0], beneficiary=k[1], date=k[2], currency=k[3],
                 payment_ids=[r['payment_id'] for r in rows], count=len(rows),
                 total=str(sum(Decimal(r['amount']) for r in rows)))
            for k, rows in groups.items() if len(rows) > 1]
mismatches = [r['payment_id'] for r in payments
              if r['beneficiary_country'] in name_codes
              and name_codes[r['beneficiary_country']] != r['beneficiary_country_code']]
result = {
    'payment_rows': len(payments), 'client_rows': len(clients),
    'clients_with_payments': len({r['client_id'] for r in payments}),
    'unknown_client_ids': sorted({r['client_id'] for r in payments} - client_ids),
    'duplicate_payment_ids': [k for k,v in Counter(r['payment_id'] for r in payments).items() if v > 1],
    'duplicate_client_ids': [k for k,v in Counter(r['client_id'] for r in clients).items() if v > 1],
    'blank_cells': sum(v == '' for r in payments + clients for v in r.values()),
    'nonpositive_amounts': [r['payment_id'] for r in payments if Decimal(r['amount']) <= 0],
    'currencies': dict(Counter(r['currency'] for r in payments)),
    'date_range': [min(r['payment_date'] for r in payments), max(r['payment_date'] for r in payments)],
    'destination_codes': dict(Counter(r['beneficiary_country_code'] for r in payments)),
    'country_name_code_mismatch_count': len(mismatches),
    'country_name_code_mismatch_ids': mismatches,
    'unmapped_country_names': sorted({r['beneficiary_country'] for r in payments} - set(name_codes)),
    'repeated_client_beneficiary_date_currency_groups': repeated,
    'c2003_same_date_rows': [r for r in payments if r['client_id'] == 'C2003' and r['payment_date'] == '2026-04-11'],
    'northstar_same_date_rows': [r for r in payments if r['beneficiary_name'] == 'Northstar Trading' and r['payment_date'] == '2026-04-11'],
    'limitations': 'Grouping uses calendar date and native currency, not true rolling 24h or FX-adjusted totals. No suspicious-activity or review determinations are made.'
}
print(json.dumps(result, indent=2))
