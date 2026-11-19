# -*- coding: utf-8 -*-
"""
Модель тактового генератора ШИМ как бинарной последовательной композиции A∙B
и трансляция теста хвостовой компоненты через головную.

A - счетчик по модулю M с разрешением счета: вход en (0 - хранение, 1 - счет),
    выход - новое значение счетчика c (канал U = {0, ..., M-1}).
B - компаратор с RS-триггером: состояние q (0/1); при c = 0 триггер устанавливается (q = 1),
    при c = h сбрасывается (q = 0), иначе хранит значение; выход pwm = новое значение q.
    Таким образом, pwm = 1, пока счетчик идет от 0 до h-1.

Запуск файла выводит таблицы автоматов A, B и автомата-композиции для заданных M и h:
    python pwm_model.py 8 3
"""
import argparse


def counter(M):
    """счетчик по модулю M: delta[c][en], lam[c][en]"""
    return [[c, (c + 1) % M] for c in range(M)], [[c, (c + 1) % M] for c in range(M)]


def pwm(M, h):
    """компаратор + RS-триггер: delta[q][c], lam[q][c]"""
    d, l = [], []
    for q in range(2):
        rd, rl = [], []
        for v in range(M):
            q2 = 1 if v == 0 else (0 if v == h else q)
            rd.append(q2); rl.append(q2)
        d.append(rd); l.append(rl)
    return d, l


def admissible_prefix(A, beta, pI):
    """длина наибольшего префикса последовательности beta (в алфавите U), который автомат A
    может выдать из начального состояния при некоторой входной последовательности"""
    dA, lA = A
    S = {0}
    for k, u in enumerate(beta):
        S = {dA[a][i] for a in S for i in range(pI) if lA[a][i] == u}
        if not S: return k
    return len(beta)


def translate(A, beta, p):
    """трансляция последовательности beta через A (обратный автомат): входная последовательность A,
    порождающая наибольший допустимый префикс beta"""
    dA, lA = A
    cur = {0: []}
    for u in beta:
        nxt = {}
        for a, alpha in cur.items():
            for i in range(p):
                if lA[a][i] == u and dA[a][i] not in nxt:
                    nxt[dA[a][i]] = alpha + [i]
        if not nxt: break
        cur = nxt
    return next(iter(cur.values()))


def table(name, fsm, in_names, out_names, state_names=None):
    d, l = fsm
    rows = [f'# {name}: состояние, вход -> следующее состояние / выход']
    for s in range(len(d)):
        sn = state_names[s] if state_names else str(s)
        for i in range(len(d[s])):
            tn = state_names[d[s][i]] if state_names else str(d[s][i])
            rows.append(f'{sn}\t{in_names[i]}\t-> {tn}\t/ {out_names[l[s][i]]}')
    return '\n'.join(rows)


def main():
    ap = argparse.ArgumentParser(description='Таблицы автоматов генератора ШИМ')
    ap.add_argument('M', nargs='?', type=int, default=8, help='период счетчика (по умолчанию 8)')
    ap.add_argument('h', nargs='?', type=int, default=3, help='порог: pwm = 1 при значениях счетчика 0..h-1 (по умолчанию 3)')
    a = ap.parse_args()
    M, h = a.M, a.h
    from fsmnet import Net
    A, B = counter(M), pwm(M, h)
    print(f'Генератор ШИМ: M = {M}, h = {h}\n')
    print(table('A (счетчик)', A, ['s', 'c'], [str(c) for c in range(M)]))
    print('# вход s - хранение (en = 0), c - счет (en = 1)\n')
    print(table('B (компаратор + RS-триггер)', B, [str(c) for c in range(M)], ['0', '1']))
    print()
    net = Net(A, B, 2, pU=M, pO=2)
    names = [f'({a}, {b})' for (a, b) in net.st]
    spec = (net.nxt, [[net.lB[b][u] for (b, u) in row] for row in net.lab])
    print(table(f'Spec = A∙B (достижимо {net.r} из {M * 2} пар состояний)', spec, ['s', 'c'], ['0', '1'], names))


if __name__ == '__main__':
    main()
