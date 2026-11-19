#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сводка результатов экспериментов в виде чисел, приведенных в статье.
Читает файлы из каталога results (по умолчанию) или из каталога, указанного аргументом:
    python report.py [каталог]
"""
import argparse
import json
import os

R = 'results'


def load(name):
    with open(os.path.join(R, name), encoding='utf-8') as f:
        return json.load(f)


def pct(x, d=1):
    return f'{100 * x:.{d}f}'.replace('.', ',') + ' %'


def num(x):
    return f'{x:,}'.replace(',', ' ')


def pwm_series():
    a = load('pwm_series_a.json')
    b = load('pwm_series_b.json')
    print('=== Генератор ШИМ (п. 3.3, рис. 12-14) ===')
    hdr = f"{'M':>3} {'h':>2} {'r':>3} {'n':>3} {'W':>9} {'HSI':>9} {'HSI/W':>7} {'MB1':>4} {'MB12':>5} {'MBC':>4}"
    for title, rs in (('серия (а): M = 4..16, h = ceil(3M/8)', a), ('серия (б): M = 8, h = 1..7', b)):
        print(title)
        print(hdr)
        for r in rs:
            print(f"{r['M']:>3} {r['h']:>2} {r['r']:>3} {r['n']:>3} {num(r['W_len']):>9} {num(r['HSI_len']):>9} "
                  f"{pct(r['HSI_len'] / r['W_len'], 0):>7} {r['MB1_len']:>4} {r['MB12_len']:>5} {r['MBC_len']:>4}")
    r8 = [r for r in a if (r['M'], r['h']) == (8, 3)][0]
    print(f"\nM = 8, h = 3: достижимо {r8['r']} из {r8['NK']} пар состояний; обнаружимых мутантов "
          f"1/2/3-го порядка: {r8['m1_dist']}/{r8['m2_dist']}/{r8['m3_dist']} из {r8['m1_total']}/{r8['m2_total']}/{r8['m3_total']}")
    for name in ('MB1', 'MB12', 'MBC', 'HSI', 'W'):
        ln = r8[name + '_len']
        print(f"  {name:5} длина {num(ln):>6}: " + ', '.join(pct(r8[f'{name}_det{l}'] / r8[f'm{l}_dist']) for l in (1, 2, 3)))
    print('\nтесты B в изоляции, подача через счетчик (последовательности целиком / символы):')
    for r in a:
        print(f"  M = {r['M']:2d}: W-тест {pct(r['isoW_seq'], 0)} / {pct(r['isoW_sym'], 0)}, "
              f"MB12 {pct(r['isoMB12_seq'], 0)} / {pct(r['isoMB12_sym'], 0)}")
    print('полнота тестов B в изоляции после трансляции через счетчик (1/2/3-й порядок):')
    for r in a:
        print(f"  M = {r['M']:2d}: W-тест " + ', '.join(pct(r[f'isoW_ttdet{l}'] / r[f'm{l}_dist'], 0) for l in (1, 2, 3)) +
              '; MB12 ' + ', '.join(pct(r[f'isoMB12_ttdet{l}'] / r[f'm{l}_dist'], 0) for l in (1, 2, 3)))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Сводка результатов экспериментов с генератором ШИМ')
    ap.add_argument('dir', nargs='?', default='results', help='каталог с результатами (по умолчанию %(default)s)')
    R = ap.parse_args().dir
    pwm_series()
