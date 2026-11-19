#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Рисунки 12-14 статьи по результатам exp_pwm.py (черно-белые, 300 dpi).
    python plots.py [results] [figures]
Нужен matplotlib.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker

_ap = argparse.ArgumentParser(description='Рисунки 12-14 статьи по результатам exp_pwm.py')
_ap.add_argument('results', nargs='?', default='results', help='каталог с результатами (по умолчанию %(default)s)')
_ap.add_argument('figures', nargs='?', default='figures', help='каталог для рисунков (по умолчанию %(default)s)')
_args = _ap.parse_args()
R, OUT = _args.results, _args.figures
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(R, 'pwm_series_a.json'), encoding='utf-8') as f:
    RM = json.load(f)

INK = '#000000'; AX = '#333333'; GRID = '#d9d9d9'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'mathtext.fontset': 'dejavusans',
                     'axes.edgecolor': AX, 'axes.linewidth': 0.8})
fmt = lambda v: f'{v:,}'.replace(',', ' ') if isinstance(v, int) else f'{v}'.replace('.', ',')
ST = {'W':    dict(color='#000000', ls='-',          marker='o', mfc='#000000', label='W'),
      'HSI':  dict(color='#7a7a7a', ls=(0, (6, 3)),  marker='s', mfc='white',   label='HSI'),
      'MB1':  dict(color='#000000', ls='-',          marker='^', mfc='white',   label='MB1'),
      'MB12': dict(color='#555555', ls=(0, (2, 2)),  marker='D', mfc='#555555', label='MB12')}
DPI = 300


def style(ax, ylabel, xlabel):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    ax.tick_params(colors=INK, labelsize=8.5)
    ax.yaxis.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.set_ylabel(ylabel, color=INK); ax.set_xlabel(xlabel, color=INK)


def line(ax, xs, ys, key):
    s = ST[key]
    ax.plot(xs, ys, color=s['color'], ls=s['ls'], lw=1.3, label=s['label'], marker=s['marker'], ms=4.5,
            mfc=s['mfc'], mec=s['color'], mew=0.9, zorder=3)


def fig_len():
    """рис. 12: длина тестов в серии (а), логарифмическая шкала"""
    fig, ax = plt.subplots(figsize=(4.7, 2.75), dpi=DPI)
    xs = [r['M'] for r in RM]
    for k in ('W', 'HSI', 'MB1', 'MB12'):
        line(ax, xs, [r[k + '_len'] for r in RM], k)
    ax.set_yscale('log'); ax.yaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.set_ylim(8, 4e6)
    style(ax, 'Длина теста, такты', 'Период счетчика $M$ ($h$ ≈ 3$M$/8)')
    ax.set_xticks(xs)
    last, first = RM[-1], RM[0]
    for k, o in (('W', 1.9), ('HSI', 0.55), ('MB1', 0.8), ('MB12', 1.3)):
        v = last[k + '_len']
        ax.annotate(fmt(v), (xs[-1], v * o), xytext=(6, 0), textcoords='offset points', fontsize=7.5, color=INK, va='center', ha='left')
    for k, o in (('W', 1.9), ('HSI', 0.52)):
        v = first[k + '_len']
        ax.annotate(fmt(v), (xs[0], v * o), xytext=(-6, 0), textcoords='offset points', fontsize=7.5, color=INK, va='center', ha='right')
    ax.set_xlim(xs[0] - (xs[-1] - xs[0]) * 0.11, xs[-1] + (xs[-1] - xs[0]) * 0.17)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.17), ncol=4, frameon=False, fontsize=8.5, handlelength=2.8, columnspacing=1.2)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig12_pwm_len.png'), facecolor='white'); plt.close(fig)


def fig_cov():
    """рис. 13: доля обнаруженных отличимых мутантов при M = 8, h = 3"""
    r = [x for x in RM if x['M'] == 8][0]
    tests = [('MB1', dict(color='white', edgecolor=INK, hatch='')),
             ('MB12', dict(color='#bfbfbf', edgecolor=INK, hatch='////')),
             ('HSI', dict(color='#808080', edgecolor=INK, hatch='')),
             ('W', dict(color='#262626', edgecolor=INK, hatch=''))]
    fig, ax = plt.subplots(figsize=(4.7, 2.75), dpi=DPI)
    w = 0.19
    for k, (key, kw) in enumerate(tests):
        ys = [100 * r[f'{key}_det{o}'] / r[f'm{o}_dist'] for o in '123']
        xs = [j + (k - 1.5) * w for j in range(3)]
        ax.bar(xs, ys, width=w * 0.88, linewidth=0.8, label=f'{key} ({fmt(r[key + "_len"])})', **kw)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.08, f'{y:.1f}'.replace('.', ','), ha='center', va='bottom', fontsize=7, color=INK, rotation=90)
    ax.set_xticks(range(3)); ax.set_xticklabels(['1-й порядок', '2-й порядок', '3-й порядок'])
    ax.set_ylim(97, 100.95); ax.set_yticks([97, 98, 99, 100])
    style(ax, 'Обнаружено мутантов, %', '')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False, fontsize=8, handlelength=1.4, columnspacing=0.9, handletextpad=0.4)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig13_pwm_cov.png'), facecolor='white'); plt.close(fig)


def fig_iso():
    """рис. 14: доля теста изолированной компоненты B, подаваемая через счетчик"""
    fig, ax = plt.subplots(figsize=(4.7, 2.95), dpi=DPI)
    xs = [r['M'] for r in RM]
    for key, lab, c, m in (('isoW', 'W-тест', '#000000', 'o'), ('isoMB12', 'MB12-тест', '#6e6e6e', 's')):
        ax.plot(xs, [100 * r[key + '_sym'] for r in RM], color=c, lw=1.3, marker=m, ms=4.5, mfc=c, mec=c, label=lab + ': символы')
        ax.plot(xs, [100 * r[key + '_seq'] for r in RM], color=c, lw=1.3, ls=(0, (6, 3)), marker=m, ms=4.5, mfc='white', mec=c, mew=1.1,
                label=lab + ': последовательности')
    ax.set_xticks(xs); ax.set_ylim(0, 100)
    style(ax, 'Подается через счетчик, %', 'Период счетчика $M$')
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), frameon=False, fontsize=8, ncol=2, handlelength=2.6, columnspacing=1.0)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, 'fig14_pwm_iso.png'), facecolor='white'); plt.close(fig)


if __name__ == '__main__':
    fig_len(); fig_cov(); fig_iso()
    print('рисунки в каталоге', OUT)
