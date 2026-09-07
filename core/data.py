"""Validated, immutable synthetic source snapshot. No external data access."""
import csv
import hashlib
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'reference'

class DataError(ValueError):
    pass

class Store:
    def __init__(self, directory=REFERENCE):
        self.directory = Path(directory)
        self.clients = self._load('clients.csv', 'client_id')
        self.payments = self._load('payments.csv', 'payment_id')
        for payment in self.payments.values():
            if payment['client_id'] not in self.clients:
                raise DataError('Payment references an unknown client')
            try:
                amount = Decimal(payment['amount'])
                if not amount.is_finite() or amount <= 0:
                    raise DataError('Invalid payment amount')
                date.fromisoformat(payment['payment_date'])
            except (InvalidOperation, ValueError) as exc:
                raise DataError('Invalid amount or date in source') from exc
        paths = sorted(self.directory.glob('*.csv')) + sorted((self.directory / 'policies').glob('*.md'))
        self.version = hashlib.sha256(b''.join(p.name.encode() + p.read_bytes() for p in paths)).hexdigest()[:16]

    def _load(self, filename, key):
        with (self.directory / filename).open(encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        output = {}
        for row in rows:
            if not row.get(key) or any(v is None or v == '' for v in row.values()):
                raise DataError('Source contains missing fields')
            if row[key] in output:
                raise DataError('Source contains duplicate identifiers')
            output[row[key]] = row
        return output

STORE = Store()
