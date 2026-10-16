#!/usr/bin/env python3
"""Render the paper's verified scores as deterministic, dependency-free SVGs."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ('average', 'base', 'delta', 'condition', 'environment', 'observation', 'execution', 'robot', 'language')


def render(setting, rows):
    rows = sorted(rows, key=lambda row: -float(row['average']))
    accent = '#2563eb' if setting == 'static' else '#087f8c'
    rgb = '37,99,235' if setting == 'static' else '8,127,140'
    title = 'Static distribution shifts' if setting == 'static' else 'Runtime distribution shifts'
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1760" height="1140" viewBox="0 0 1760 1140" role="img" aria-labelledby="title desc">',
           f'<title id="title">{title}: all 17 policies ranked by average success</title>',
           '<desc id="desc">Paper scores in percent. Bars show average success on a zero to one hundred scale; shaded cells show category success. Bold category values mark column maxima. Delta is average minus base, reported before rounding.</desc>',
           '<style>text{font-family:Arial,Helvetica,sans-serif;font-variant-numeric:tabular-nums} .number{font-family:Arial,Helvetica,sans-serif}</style>',
           '<rect x="1" y="1" width="1758" height="1138" rx="20" fill="#ffffff" stroke="#dce3ed"/>',
           f'<path d="M24 1H1736" stroke="{accent}" stroke-width="3"/>']
    def text(x, y, value, size=22, fill='#172b45', weight=400, anchor='start', extra=''):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{html.escape(str(value))}</text>')
    def rect(x, y, w, h, fill, radius=0, extra=''):
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" {extra}/>')
    text(38, 46, 'LIBERO-Pro2.0  /  LEADERBOARD', 17, accent, 700, extra='letter-spacing="2"')
    text(38, 97, title, 36, weight=700)
    text(38, 132, '17 policies · Paper results · Success rate (%)', 20, '#65758b')
    rect(1455, 64, 265, 45, '#f1f5f9', 22)
    text(1587, 93, 'Higher is better  ↑', 20, accent, 600, 'middle')
    out.append('<path d="M38 158H1722" stroke="#dce3ed"/>')
    text(397, 190, 'OVERALL PERFORMANCE', 15, accent, 700, extra='letter-spacing="1.5"')
    text(874, 190, 'SUCCESS UNDER PERTURBATIONS', 15, '#65758b', 700, extra='letter-spacing="1.5"')
    # Column labels deliberately have a fixed line and cannot wrap on GitHub.
    text(65, 233, '#', 19, '#65758b', 600, 'middle')
    text(105, 233, 'Policy', 21, weight=600)
    text(490, 233, 'Average ↑', 21, accent, 700, 'middle')
    text(672, 233, 'Base', 21, '#65758b', 600, 'middle')
    text(779, 233, 'Δ (pp)', 21, '#65758b', 600, 'middle')
    category_x = [939, 1081, 1223, 1365, 1507, 1649]
    labels = ['Condition', 'Environment', 'Observation', 'Execution', 'Robot', 'Language']
    for x, label in zip(category_x, labels):
        text(x, 233, label, 19, '#65758b', 600, 'middle')
    maxima = {key: max(float(row[key]) for row in rows) for key in FIELDS if key != 'delta'}
    for rank, row in enumerate(rows, 1):
        top = 253 + (rank-1)*47
        baseline = top+30
        out.append(f'<g data-model="{html.escape(row["model"], quote=True)}">')
        if rank % 2:
            rect(24, top, 1712, 47, '#f7f9fc', 6)
        if rank <= 3:
            rect(48, top+8, 34, 31, f'rgba({rgb},0.10)', 8)
        text(65, baseline, rank, 20, accent if rank <= 3 else '#7b899b', 700 if rank <= 3 else 400, 'middle')
        text(105, baseline, row['model'], 23, weight=600 if rank <= 3 else 400)
        rect(397, top+19, 138, 9, '#e3eaf3', 4)
        rect(397, top+19, round(138*float(row['average'])/100, 3), 9, accent, 4)
        text(605, baseline, row['average'], 24, accent, 700, 'end', 'data-field="average"')
        text(672, baseline, row['base'], 22, '#53657d', 700 if float(row['base']) == maxima['base'] else 400, 'middle', 'data-field="base"')
        text(779, baseline, row['delta'], 21, '#9a5660', 400, 'middle', 'data-field="delta"')
        for x, key in zip(category_x, FIELDS[3:]):
            value = float(row[key])
            rect(x-58, top+6, 116, 35, f'rgba({rgb},{0.025+value/100*0.16:.4f})', 7)
            text(x, baseline, row[key], 23, '#172b45', 700 if value == maxima[key] else 400, 'middle', f'data-field="{key}"')
        out.append('</g>')
    out.append('<path d="M38 1068H1722" stroke="#dce3ed"/>')
    text(38, 1109, 'Bars: average success / 100', 18, '#65758b')
    text(575, 1109, 'Cell shading: category success', 18, '#65758b')
    text(1722, 1109, 'Bold: column best · Δ: reported before rounding', 18, '#65758b', anchor='end')
    out.append('</svg>\n')
    target = ROOT / 'static' / 'leaderboards' / f'{setting}.svg'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(out))


if __name__ == '__main__':
    source = json.loads((ROOT / 'docs/results/paper-leaderboards.json').read_text())
    for setting in ('static', 'runtime'):
        render(setting, source['tables'][setting])
