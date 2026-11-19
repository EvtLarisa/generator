#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Эксперименты с генератором ШИМ (п. 3.3 статьи, рис. 12-14).

Композиция: A - счетчик по модулю M (вход en), B - компаратор + RS-триггер (pwm_model.py).
Мутанты B: все мутанты первого, второго и третьего порядков (ошибки переходов и выходов),
полнота считается относительно мутантов, обнаружимых через контекст.

Тесты по Spec = A∙B: W и HSI (полные относительно реализаций с не более чем NK = 2M состояниями),
MB1, MB12, MBC (см. fsmnet.py).
Тесты B в изоляции: W-тест (m = K = 2) и MB12 автомата B; для них считаются доля последовательностей,
которые можно подать через счетчик целиком, доля символов, доходящих до B, и полнота теста
после трансляции через счетчик.

Серии: (а) M = 4, 6, ..., 16, h = ceil(3M/8); (б) M = 8, h = 1, ..., 7.
Полнота W- и HSI-тестов проверяется при M <= 8 (при больших M тесты слишком длинные).

    python exp_pwm.py [каталог результатов, по умолчанию results]
Время счета около 15 секунд.
"""
import argparse
import json
import math
import os
import time

from fsmnet import Net, mb, length, single_faults, order_k
from wmethod import w_hsi
from pwm_model import counter, pwm, admissible_prefix, translate


def experiment(Mc, h, check_w=True):
    t0 = time.time()
    A, B = counter(Mc), pwm(Mc, h)
    net = Net(A, B, 2, pU=Mc, pO=2)
    N, K = Mc, 2
    rec = dict(M=Mc, h=h, N=N, K=K, NK=N * K, r=net.r, used=len(net.used), transB=K * Mc)
    fs = single_faults(net)
    m = {}
    for lvl in (1, 2, 3):
        allm = [net.mutant(list(c)) for c in order_k(net, fs, lvl)]
        m[lvl] = [M for M in allm if net.distinguishable(M)]
        rec[f'm{lvl}_total'] = len(allm); rec[f'm{lvl}_dist'] = len(m[lvl])
    m1_all = [net.mutant([f]) for f in fs]
    m2_all = [net.mutant(list(c)) for c in order_k(net, fs, 2)]
    # мутационные тесты по Spec
    tour = net.cpp_tour()
    rec['tour'] = length(tour)
    T1, a1 = mb(net, tour, m1_all, ext=False)
    T12, a12 = mb(net, T1, m2_all, ext=False)
    TC, _ = mb(net, net.comp_cover(), m1_all, ext=True)
    tests = {'MB1': T1, 'MB12': T12, 'MBC': TC}
    for name, T in tests.items():
        rec[name + '_len'] = length(T); rec[name + '_cnt'] = len(T)
        for lvl in (1, 2, 3):
            rec[f'{name}_det{lvl}'] = sum(net.detects(T, M) for M in m[lvl])
    rec['MB1_added'] = a1; rec['MB12_added'] = a12
    # NK-полные W- и HSI-тесты
    wh, Wt, Ht = w_hsi(net, N * K)
    rec.update(wh)
    if check_w:
        for name, T in (('W', Wt), ('HSI', Ht)):
            for lvl in (1, 2, 3):
                rec[f'{name}_det{lvl}'] = sum(net.detects(T, M) for M in m[lvl])
    # тесты B в изоляции и их трансляция через счетчик
    ident = ([[0] * Mc], [list(range(Mc))])
    nb = Net(ident, B, Mc, pU=Mc, pO=2)
    fb = single_faults(nb)
    TB1, _ = mb(nb, nb.cpp_tour(), [nb.mutant([f]) for f in fb], ext=False)
    TB12, _ = mb(nb, TB1, [nb.mutant(list(c)) for c in order_k(nb, fb, 2)], ext=False)
    _, WBt, _ = w_hsi(nb, K)
    for name, T in (('isoW', WBt), ('isoMB12', TB12)):
        pref = [admissible_prefix(A, s, 2) for s in T]
        rec[name + '_cnt'] = len(T); rec[name + '_len'] = length(T)
        rec[name + '_seq'] = sum(pf == len(s) for pf, s in zip(pref, T)) / len(T)
        rec[name + '_sym'] = sum(pref) / sum(len(s) for s in T)
        TT = [a for a in (translate(A, b, 2) for b in T) if a]
        rec[name + '_ttlen'] = length(TT)
        for lvl in (1, 2, 3):
            rec[f'{name}_ttdet{lvl}'] = sum(net.detects(TT, M) for M in m[lvl])
    rec['time'] = round(time.time() - t0, 3)
    return rec, dict(tour=tour, MB1=T1, MB12=T12, MBC=TC)


def main():
    ap = argparse.ArgumentParser(description='Эксперименты с генератором ШИМ, серии (а) и (б)')
    ap.add_argument('out', nargs='?', default='results', help='каталог результатов (по умолчанию %(default)s)')
    out = ap.parse_args().out
    os.makedirs(out, exist_ok=True)
    series = {
        'pwm_series_a.json': [(M, math.ceil(3 * M / 8)) for M in range(4, 17, 2)],
        'pwm_series_b.json': [(8, h) for h in range(1, 8)],
    }
    for fname, params in series.items():
        recs = []
        for Mc, h in params:
            rec, tests = experiment(Mc, h, check_w=(Mc <= 8))
            recs.append(rec)
            print(f"M = {Mc:2d}, h = {h}: r = {rec['r']}, W = {rec['W_len']}, HSI = {rec['HSI_len']}, "
                  f"MB1 = {rec['MB1_len']}, MB12 = {rec['MB12_len']}", flush=True)
            if (Mc, h) == (8, 3) and fname == 'pwm_series_a.json':
                with open(os.path.join(out, 'pwm_tests_M8_h3.json'), 'w', encoding='utf-8') as f:
                    json.dump(tests, f)
        with open(os.path.join(out, fname), 'w', encoding='utf-8') as f:
            json.dump(recs, f, indent=0)
    print('результаты в каталоге', out)


if __name__ == '__main__':
    main()
