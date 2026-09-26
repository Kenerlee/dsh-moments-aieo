#!/usr/bin/env python3
"""Pack the evidence zip that ships next to the client HTML, using only the stdlib.

Contents: the _含证据附录 edition, report .json/.metrics.json, the question bank, evidence/ and any --extra files.
The client edition is never packed. zipfile writes UTF-8 names, so Chinese filenames survive on Windows
(macOS `zip` does not set that flag).
"""
import argparse
import fnmatch
import json
from pathlib import Path
import zipfile


def package(report, extras=(), exclude=()):
    report = Path(report)
    root = report.parent
    d = json.loads(report.read_text(encoding='utf-8'))
    full = root / f'{report.stem}_含证据附录.html'
    if not full.is_file():
        raise SystemExit(f'missing {full.name}: run render_report.py first')
    files = [full, report, report.with_suffix('.metrics.json')]
    files += sorted(root.glob(f'{d["target"]}_问题库_*.md'))
    files += [root / x for x in extras]
    evidence = root / 'evidence'
    if evidence.exists():
        files += sorted(p for p in evidence.rglob('*') if p.is_file())
    files = [f for f in files if f.is_file() and not any(fnmatch.fnmatch(f.name, pat) for pat in exclude)]
    if report.with_suffix('.html') in files:
        raise SystemExit('the client edition must not be inside the evidence zip')
    out = root / f'{d["target"]}_AIEO诊断_完整证据_{d["date"]}.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in dict.fromkeys(files):
            z.write(f, f.relative_to(root).as_posix())
    return out, len(files)


def check():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'evidence/a').mkdir(parents=True)
        (root / 'evidence/a/answer.png').write_bytes(b'png')
        (root / 'evidence/report-old.png').write_bytes(b'png')
        report = root / '甲_AIEO诊断报告_2026-09-26.json'
        report.write_text(json.dumps(dict(target='甲', date='2026-09-26')), encoding='utf-8')
        for name in ('甲_AIEO诊断报告_2026-09-26.html', '甲_AIEO诊断报告_2026-09-26_含证据附录.html',
                     '甲_AIEO诊断报告_2026-09-26.metrics.json', '甲_问题库_2026-09-26.md', '技术说明.md'):
            (root / name).write_text('x', encoding='utf-8')
        out, n = package(report, ['技术说明.md'], ['report-*.png'])
        z = zipfile.ZipFile(out)
        names = z.namelist()
        assert '甲_AIEO诊断报告_2026-09-26.html' not in names, 'client edition excluded'
        assert '甲_AIEO诊断报告_2026-09-26_含证据附录.html' in names and '甲_问题库_2026-09-26.md' in names and '技术说明.md' in names
        assert 'evidence/a/answer.png' in names and 'evidence/report-old.png' not in names
        assert all(i.flag_bits & 0x800 for i in z.infolist() if not i.filename.isascii()), 'UTF-8 filename flag set'
    print('PASS: contents, client edition excluded, exclude patterns, UTF-8 names')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', nargs='?', type=Path, help='the report .json next to both HTML editions')
    parser.add_argument('--extra', action='append', default=[], help='extra file in the report folder to include (repeatable)')
    parser.add_argument('--exclude', action='append', default=[], help='filename glob to leave out (repeatable)')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        check()
        return
    if args.report is None:
        parser.error('provide the report .json or --check')
    out, n = package(args.report, args.extra, args.exclude)
    print(f'{out} ({n} files)')


if __name__ == '__main__':
    main()
