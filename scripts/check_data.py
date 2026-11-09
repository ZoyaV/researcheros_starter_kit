"""Validate provenance, target and the frozen chronological evaluation split."""
import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    protocol = json.loads((ROOT / 'data/protocol.json').read_text())
    data = ROOT / 'data/advertising.csv'
    assert hashlib.sha256(data.read_bytes()).hexdigest() == protocol['dataset_sha256'], 'Dataset checksum changed'
    with data.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames == ['row_id', *protocol['features'], protocol['target']]
    by_id = {int(row['row_id']): row for row in rows}
    assert len(by_id) == len(rows) == 9923
    assert 'row_id' not in protocol['features'] and protocol['target'] not in protocol['features']
    assert all(math.isfinite(float(row[protocol['target']])) and float(row[protocol['target']]) >= 0 for row in rows)
    groups = protocol['split']['row_ids']
    assigned = [row_id for ids in groups.values() for row_id in ids]
    assert len(assigned) == len(set(assigned)) == len(rows)
    assert set(assigned) == set(by_id), 'Split misses or duplicates rows'
    date = lambda row_id: datetime.strptime(by_id[row_id]['Дата'], '%d.%m.%Y').date()
    assert max(map(date, groups['train'])) < min(map(date, groups['validation']))
    assert max(map(date, groups['validation'])) < min(map(date, groups['test']))
    assert str(min(map(date, groups['validation']))) == protocol['split']['validation_from']
    assert str(min(map(date, groups['test']))) == protocol['split']['test_from']
    for name, ids in groups.items():
        print(f'{name}: {len(ids)} rows, {min(map(date, ids))} .. {max(map(date, ids))}')
    print('OK: dataset checksum, numeric target, complete disjoint chronological split')


if __name__ == '__main__':
    main()
