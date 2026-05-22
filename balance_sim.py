# -*- coding: utf-8 -*-
"""
東方カードゲーム 対戦シミュレーター (v3.1 / v1.3 カード)
ルールを簡易モデル化し、4リーダーから2体を選ぶ6ペアを総当たり自動対戦。
CFG で調整パラメータを変えて改善案を検証できる。
※簡易AI・簡易モデルのため、絶対値ではなく「相対傾向」を見るもの。
"""
import random

# ===== リーダー (v1.3): atk,eva, 覚醒cost, 覚醒atk,覚醒eva, 能力 =====
LD = {
 '霊夢':   (20, 11, 3, 26, 14, 'oharai'),
 '魔理沙': (21, 11, 3, 29, 12, 'koi'),
 'レミリア': (20, 10, 4, 26, 14, 'charisma'),
 'フラン': (21,  9, 4, 30, 11, 'four'),
}
PAIRS = [
 ('魔理沙','フラン'), ('魔理沙','レミリア'), ('霊夢','フラン'),
 ('霊夢','魔理沙'), ('レミリア','フラン'), ('霊夢','レミリア'),
]

CFG = {}  # 改善案テスト用の調整パラメータ
BASE_LD = {k: v for k, v in LD.items()}  # eva 上書き用の原本

# ===== スペル24種: kind, val, pp, quick, recoverP, reqLv =====
POOL = [
 ('atk',6,2,0,2,1),('atk',9,3,0,1,1),('atk',14,5,0,0,2),('atk',12,4,0,0,2),('atk',7,3,0,1,1),
 ('def',10,2,1,2,1),('def',12,3,1,1,1),('def',5,1,1,3,1),('def',20,4,1,0,2),
 ('util',2,1,0,2,1),('util',2,2,0,1,1),('util',1,2,0,0,1),
 ('disrupt',3,3,0,0,2),('mill',16,5,0,0,2),('def',10,3,0,1,1),
 ('def',6,3,1,1,1),('atk',7,2,0,1,1),('def',16,4,1,0,2),('atk',16,5,0,0,2),
 ('disrupt',2,3,0,1,1),('atk',11,4,0,0,2),('util',1,1,0,1,1),('def',8,2,1,2,1),('util',0,2,0,0,1),
]
COUNTS = [5,5,4,3,4, 4,3,3,2, 3,4,3, 3,2,3, 4,5,2,3, 2,3,3,4,3]  # 計80

def build_deck():
    d = []
    for i, c in enumerate(COUNTS):
        d += [i]*c
    random.shuffle(d)
    return d

class Side:
    def __init__(self, pair, is_first):
        self.deck = build_deck()
        self.is_first = is_first
        self.life = 3 + (0 if is_first else CFG.get('go2nd_life', 0))
        self.life_cards = [self.deck.pop() for _ in range(3)]
        self.bomb = 3
        self.P = (0 if is_first else 6) + CFG.get('go2nd_P', 0)  # 後攻補正: P6スタート
        self.hand = []
        self.trash = []
        self.turncount = 0
        self.dead = False
        n = 4 + (0 if is_first else 1 + CFG.get('go2nd_card', 0))   # 後攻補正
        for _ in range(n):
            if self.deck:
                self.hand.append(self.deck.pop(0))
        self.leaders = [{'k':k,'aw':False,'rested':False,'awThis':False} for k in pair]

def draw(s, n):
    for _ in range(n):
        if not s.deck:
            refresh(s)
            if s.dead: return
        if s.deck:
            s.hand.append(s.deck.pop(0))

def refresh(s):
    s.deck = s.trash
    s.trash = []
    random.shuffle(s.deck)
    s.life -= 1
    if s.life_cards:
        s.hand.append(s.life_cards.pop())
    if s.life <= 0:
        s.dead = True

def mill(s, n):
    milled = []
    for _ in range(n):
        if not s.deck:
            refresh(s)
            if s.dead:
                return milled
        if not s.deck:
            break
        c = s.deck.pop(0)
        s.trash.append(c)
        milled.append(c)
    return milled

def lv_ok(s, lv):
    return lv <= 1 or any(L['aw'] for L in s.leaders)

def has_quick_def(s):
    return any(POOL[c][0]=='def' and POOL[c][3]==1 for c in s.hand)

def covenant(s, o):
    cand = [L for L in s.leaders if not L['aw']]
    if not cand: return
    cand.sort(key=lambda L: LD[L['k']][3], reverse=True)
    L = cand[0]
    cost = LD[L['k']][2]
    aid = next((c for c in s.hand if POOL[c][0]=='util' and POOL[c][1]==0 and POOL[c][2]<=s.P), None)
    eff = cost
    if aid is not None and cost-2 <= s.P < cost:
        s.P -= POOL[aid][2]; s.hand.remove(aid); s.trash.append(aid); eff = cost-2
    if s.P < eff: return
    s.P -= eff
    L['aw'] = True; L['awThis'] = True
    ab = LD[L['k']][5]
    if ab == 'oharai':
        if o.hand: o.trash.append(o.hand.pop(random.randrange(len(o.hand))))
        draw(s, 1)
    elif ab == 'charisma':
        mill(o, CFG.get('gungnir', 5))
    elif ab == 'four':
        mill(o, 8)
        for _ in range(2):
            if s.hand: s.trash.append(s.hand.pop(random.randrange(len(s.hand))))

def best_def(o):
    ready = [L for L in o.leaders if not L['rested']]
    pool = ready if ready else o.leaders
    def eva(L):
        a,e,_,_,ae,_ = LD[L['k']]
        return ae if L['aw'] else e
    return max(pool, key=eva)

def take_turn(s, o):
    s.turncount += 1
    for L in s.leaders:
        L['rested'] = False; L['awThis'] = False
    if not (s.is_first and s.turncount == 1):
        draw(s, 1)
    if s.dead: return
    if s.hand:   # チャージ: 手札1枚をPへ、1枚ドロー
        s.P += 1
        order = sorted(range(len(s.hand)), key=lambda i: (POOL[s.hand[i]][0]!='util', POOL[s.hand[i]][1]))
        s.hand.pop(order[0])
        draw(s, 1)
        if s.dead: return
    if s.turncount >= 2:
        covenant(s, o)
        if s.dead or o.dead: return
    # 攻撃 (テスト設定: 先攻初ターンの攻撃をスキップ)
    if CFG.get('first_no_t1_atk') and s.is_first and s.turncount == 1:
        return
    do_attack(s, o)
    if CFG.get('go2nd_t1_double') and (not s.is_first) and s.turncount == 1 and not s.dead and not o.dead:
        do_attack(s, o)

def do_attack(s, o):
    def leader_val(L):
        a,e,awc,aatk,aeva,ab = LD[L['k']]
        base = aatk if L['aw'] else a
        if ab == 'koi': base += CFG.get('koi', 4)
        if ab == 'four': base += CFG.get('four', 6)
        if ab == 'koi' and L['awThis']: base += 8
        virt = 0
        if ab == 'oharai':
            virt = 3 if o.P > 0 else CFG.get('oharai_dmg', 0)
        if ab == 'charisma': virt = 2
        return base, virt, ab
    scored = [(leader_val(L), L) for L in s.leaders]
    scored.sort(key=lambda x: x[0][0]+x[0][1], reverse=True)
    (base, virt, ab), atkL = scored[0]
    reserve = 2 if has_quick_def(s) else 0
    budget = max(0, s.P - reserve)
    spell_bonus = 0; direct = 0
    atk_cards = sorted([c for c in s.hand if POOL[c][0] in ('atk','mill') and lv_ok(s, POOL[c][5])],
                       key=lambda c: POOL[c][1], reverse=True)
    for c in atk_cards:
        k,val,pp,_,_,_ = POOL[c]
        if pp <= budget:
            budget -= pp
            s.hand.remove(c); s.trash.append(c)
            if k == 'atk': spell_bonus += val
            else: direct += val
    s.P = budget + reserve
    dL = best_def(o)
    da,de,_,_,dae,_ = LD[dL['k']]
    dval = dae if dL['aw'] else de
    raw = base + spell_bonus + (CFG.get('oharai_dmg', 0) if (ab == 'oharai' and o.P < 2) else 0)
    reduce = 0
    quick = sorted([c for c in o.hand if POOL[c][0]=='def' and POOL[c][3]==1 and lv_ok(o, POOL[c][5])],
                   key=lambda c: POOL[c][1], reverse=True)
    incoming = max(1, raw - dval)
    if quick and incoming > 16 and POOL[quick[0]][2] <= o.P:
        c = quick[0]
        o.P -= POOL[c][2]; o.hand.remove(c); o.trash.append(c)
        reduce += POOL[c][1]
    incoming = max(1, raw - dval - reduce)
    use_bomb = o.bomb >= 2 and incoming >= len(o.deck) and o.life <= 1
    if use_bomb: o.bomb -= 2
    final = 0 if use_bomb else max(1, raw - dval - reduce)
    if CFG.get('first_t1_atk_half') and s.is_first and s.turncount == 1:
        final = max(1, final // 2)
    if final > 0:
        milled = mill(o, final)
        s.P += min(sum(POOL[c][4] for c in milled), 3)
    if direct > 0 and not o.dead:
        mill(o, direct)
    if ab == 'four':
        mill(s, 2)
    elif ab == 'oharai':
        o.P = max(0, o.P - 2)
    elif ab == 'charisma':
        if s.trash: s.P += 1
    atkL['rested'] = True
    for c in list(s.hand):
        k,val,pp,_,_,lv = POOL[c]
        if k=='util' and pp<=s.P and lv_ok(s,lv):
            s.P -= pp; s.hand.remove(c); s.trash.append(c); draw(s, max(1,val)); break
    while len(s.hand) > 7:
        s.trash.append(s.hand.pop())

def play(pa, pb, n_turns=80):
    A = Side(pa, True); B = Side(pb, False)
    cur, opp = A, B
    for _ in range(n_turns):
        take_turn(cur, opp)
        if opp.dead: return 'A' if cur is A else 'B'
        if cur.dead: return 'B' if cur is A else 'A'
        cur, opp = opp, cur
    if A.life != B.life:
        return 'A' if A.life > B.life else 'B'
    return 'A' if len(A.deck)+len(A.trash) >= len(B.deck)+len(B.trash) else 'B'

def run(games_per=2000):
    names = ['+'.join(p) for p in PAIRS]
    wins = {nm:0 for nm in names}; plays = {nm:0 for nm in names}
    fw = fg = 0
    matrix = {}
    for i, pa in enumerate(PAIRS):
        for j, pb in enumerate(PAIRS):
            if i == j: continue
            aw = 0
            for _ in range(games_per):
                r = play(pa, pb); fg += 1
                if r == 'A':
                    aw += 1; wins[names[i]] += 1; fw += 1
                else:
                    wins[names[j]] += 1
                plays[names[i]] += 1; plays[names[j]] += 1
            matrix[(i,j)] = 100*aw/games_per
    rates = {nm: 100*wins[nm]/plays[nm] for nm in names}
    return 100*fw/fg, rates, matrix

if __name__ == '__main__':
    # v1.4 確定構成 (フラン攻撃+6 / 魔理沙回避11・12 / 後攻P6) の検証
    random.seed(20260522)
    first, rates, matrix = run(3000)
    print("=== v1.4 ペア別 総合勝率 (各 3000 戦/マッチ) ===")
    for nm in sorted(rates, key=lambda n: -rates[n]):
        print("  %-16s %.1f%%" % (nm, rates[nm]))
    sp = max(rates.values()) - min(rates.values())
    print("  ペア勝率幅 %.1fpt / 先攻勝率 %.1f%%" % (sp, first))
