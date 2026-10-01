#!/usr/bin/env python3
"""Compare existing SQLite rows without running submitted application code.

Copies DB plus WAL/SHM into temporary scratch before read-only SQLite access.
Added columns/tables/rows are allowed; every original row and column is checked.
This is a diagnostic only and does not alter the acceptance score.
"""
import argparse
import collections
import json
import shutil
import sqlite3
import tempfile
from pathlib import Path


def q(name):
    return '"'+name.replace('"','""')+'"'


def snapshot(db, scratch):
    target = scratch/'bakery.db'
    for suffix in ('','-wal','-shm'):
        source = Path(str(db)+suffix)
        if source.is_file():
            shutil.copy2(source, Path(str(target)+suffix))
    con = sqlite3.connect(target.as_uri()+'?mode=ro', uri=True)
    con.execute('PRAGMA query_only=ON')
    result = {'integrity_check':[r[0] for r in con.execute('PRAGMA integrity_check')], 'tables':{}}
    for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        cols = [r[1] for r in con.execute(f'PRAGMA table_info({q(table)})')]
        rows = con.execute(f'SELECT '+','.join(map(q,cols))+f' FROM {q(table)}').fetchall()
        result['tables'][table] = {'columns':cols,'rows':rows}
    con.close()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before', required=True,type=Path)
    p.add_argument('--after', required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    args = p.parse_args()
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root/'before').mkdir();(root/'after').mkdir()
        before,after = snapshot(args.before.resolve(),root/'before'),snapshot(args.after.resolve(),root/'after')
    tables = {}
    for table, old in before['tables'].items():
        new = after['tables'].get(table)
        if new is None:
            tables[table] = {'preserved':False,'reason':'Table absent','original_rows':len(old['rows'])}
            continue
        missing_cols = sorted(set(old['columns'])-set(new['columns']))
        if missing_cols:
            tables[table] = {'preserved':False,'missing_columns':missing_cols,'original_rows':len(old['rows'])}
            continue
        indices = [new['columns'].index(c) for c in old['columns']]
        old_rows = collections.Counter(tuple(r) for r in old['rows'])
        new_rows = collections.Counter(tuple(r[i] for i in indices) for r in new['rows'])
        missing = old_rows-new_rows
        extra = new_rows-old_rows
        tables[table] = {'preserved':not missing,'original_rows':len(old['rows']),'after_rows':len(new['rows']),
                         'original_rows_missing_or_changed':sum(missing.values()),'additional_or_changed_rows':sum(extra.values()),
                         'added_columns':sorted(set(new['columns'])-set(old['columns']))}
    report = {'before':str(args.before.resolve()),'after':str(args.after.resolve()),
              'before_integrity_check':before['integrity_check'],'after_integrity_check':after['integrity_check'],
              'all_original_rows_and_columns_preserved':all(t['preserved'] for t in tables.values()),
              'tables':tables,'added_tables':sorted(set(after['tables'])-set(before['tables'])),
              'scope':'Read-only diagnostic; submitted code was not executed; added rows/columns/tables allowed; quality score unchanged.'}
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
