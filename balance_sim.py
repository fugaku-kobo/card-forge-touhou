# -*- coding: utf-8 -*-
"""
東方カードゲーム 対戦シミュレーター (v3.3 / v1.5 カード・デッキ60)
ルールを簡易モデル化し、4リーダーから2体を選ぶ6ペアを総当たり自動対戦。
CFG で調整パラメータを変えて改善案を検証できる。
※簡易AI・簡易モデルのため、絶対値ではなく「相対傾向」を見るもの。

v1.5 (デッキ60): リーダー数値・スペル削り量を v1.4 から ×0.75 にスケール
                 (デッキ80→60 に伴う体感時間維持)。同 ID 上限 5→4。
"""
import random

# ===== リーダー (v1.5): atk,eva, 覚醒cost, 覚醒atk,覚醒eva, 能力 =====
LD = {
 # v3.4: 基礎値は v3.3 ベース(ペア幅 15pt 確認済み)、個性は能力レベルで尖らせる
 '霊夢':   (15,  8, 3, 20, 11, 'oharai'),    # 受け担当(夢想封印+ライフ守護)
 '魔理沙': (16,  8, 3, 22,  9, 'koi'),        # バースト型(マスタースパーク)
 'レミリア': (15,  8, 4, 20, 11, 'charisma'),  # 安定型(吸血+紅夜支配)
 'フラン': (16,  7, 4, 23,  8, 'four'),       # 代償型(フォーオブ+レーヴァテイン)
}
PAIRS = [
 ('魔理沙','フラン'), ('魔理沙','レミリア'), ('霊夢','フラン'),
 ('霊夢','魔理沙'), ('レミリア','フラン'), ('霊夢','レミリア'),
]

CFG = {}  # 改善案テスト用の調整パラメータ
BASE_LD = {k: v for k, v in LD.items()}  # eva 上書き用の原本

# ===== スペル30種 (v1.6): kind, val, pp, quick, recoverP, reqLv, lr =====
# lr = '' (共有) / '霊夢' / '魔理沙' / 'レミリア' / 'フラン' (専用)
POOL = [
 # 共有 10 種 (TH-001..010) — 基本コンバット
 ('atk',     5, 2, 0, 2, 1, ''),  # TH-001 霊符『夢想妙珠』
 ('atk',     7, 3, 0, 1, 1, ''),  # TH-002 火符『アグニシャイン』
 ('atk',    11, 5, 0, 0, 2, ''),  # TH-003 月符『サイレントセレナ』
 ('def',     4, 1, 1, 3, 1, ''),  # TH-004 結界『生死の境界』 QUICK
 ('def',     8, 2, 1, 2, 1, ''),  # TH-005 結界『博麗弾幕結界』 QUICK
 ('def',    12, 4, 1, 0, 2, ''),  # TH-006 結界『大結界』 QUICK
 ('util',    1, 1, 0, 1, 1, ''),  # TH-007 魔符『ミルキーウェイ』
 ('util',    2, 2, 0, 1, 1, ''),  # TH-008 魔符『マジカルブースター』
 ('mill',    8, 4, 0, 0, 2, ''),  # TH-009 「QED『495年の波紋』」
 ('disrupt', 1, 3, 0, 1, 2, ''),  # TH-010 幻葬『夜霧の幻影殺人鬼』
 # 霊夢専用 5 種 (TH-101..105) — 妨害&受け
 ('atk',     6, 2, 0, 1, 1, '霊夢'),  # TH-101 霊符『博麗符印』
 ('atk',    10, 4, 0, 0, 2, '霊夢'),  # TH-102 神霊『夢想封印 集』
 ('def',    10, 3, 1, 1, 2, '霊夢'),  # TH-103 結界『博麗結界』 QUICK
 ('disrupt', 2, 3, 0, 0, 1, '霊夢'),  # TH-104 神技『八方鬼縛陣』(P-3 → P-2 に調整)
 ('def',     6, 2, 1, 1, 1, '霊夢'),  # TH-105 『楽園の素敵な巫女』 QUICK
 # 魔理沙専用 5 種 (TH-201..205) — 火力バースト
 ('atk',    12, 4, 0, 0, 2, '魔理沙'),  # TH-201 恋符『マスタースパーク』 +自デッキ-2
 ('atk',    18, 5, 0, 0, 2, '魔理沙'),  # TH-202 魔砲『ファイナルスパーク』 +自デッキ-4
 ('atk',     8, 3, 0, 1, 1, '魔理沙'),  # TH-203 星符『ドラゴンメテオ』
 ('atk',     6, 2, 0, 1, 1, '魔理沙'),  # TH-204 魔符『アーティフルチャンター』
 ('util',    1, 1, 0, 1, 1, '魔理沙'),  # TH-205 『普通の魔法使い』
 # レミリア専用 5 種 (TH-301..305) — 支配&吸血
 ('atk',     8, 3, 0, 1, 1, 'レミリア'),  # TH-301 紅符『スカーレットシュート』
 ('atk',    14, 5, 0, 0, 2, 'レミリア'),  # TH-302 神槍『スピア・ザ・グングニル』 +相手P-2
 ('disrupt', 1, 3, 0, 1, 1, 'レミリア'),  # TH-303 紅魔『スカーレットデビル』
 ('util',    2, 2, 0, 1, 1, 'レミリア'),  # TH-304 吸血『ドラキュリア』
 ('def',     9, 3, 1, 0, 2, 'レミリア'),  # TH-305 『永遠に紅い幼き月』 QUICK
 # フランドール専用 5 種 (TH-401..405) — 破壊&代償
 ('atk',    10, 3, 0, 0, 1, 'フラン'),    # TH-401 禁忌『フォーオブアカインド』 +自デッキ-2
 ('mill',   15, 5, 0, 0, 2, 'フラン'),    # TH-402 禁弾『過去を刻む時計』
 ('atk',     7, 3, 0, 0, 1, 'フラン'),    # TH-403 禁忌『カゴメカゴメ』 +相手P-2
 ('atk',    15, 5, 0, 0, 2, 'フラン'),    # TH-404 禁弾『スターボウブレイク』
 ('atk',     6, 2, 0, 1, 1, 'フラン'),    # TH-405 『悪魔の妹』
]
# 専用カードの追加効果(攻撃時 self-mill / opp-P-mill)を ID で参照
EXTRA = {
    15: {'self_mill': 1},      # TH-201 マスタースパーク (代償軽減 2→1)
    16: {'self_mill': 2},      # TH-202 ファイナルスパーク (代償軽減 4→2)
    25: {'self_mill': 2},      # TH-401 フォーオブアカインド
    21: {'opp_p_mill': 2},     # TH-302 グングニル
    27: {'opp_p_mill': 2},     # TH-403 カゴメカゴメ
    10: {'opp_p_mill': 1},     # TH-101 博麗符印
}

# ペア → 該当リーダー名
LEADER_OF_PAIR = {pair: [pair[0], pair[1]] for pair in [('魔理沙','フラン'), ('魔理沙','レミリア'), ('霊夢','フラン'), ('霊夢','魔理沙'), ('レミリア','フラン'), ('霊夢','レミリア')]}

def usable_indices(pair):
    """このペアで使用可能なカードインデックス(共有+両リーダー専用) = 20種"""
    return [i for i, c in enumerate(POOL) if c[6]=='' or c[6] in pair]

def build_deck(pair):
    """v1.6 スターター: 共有10×4 + 該当ペア専用10×2 = 60枚"""
    d = []
    for i in usable_indices(pair):
        n = 4 if POOL[i][6] == '' else 2  # 共有4枚 / 専用2枚
        d += [i] * n
    random.shuffle(d)
    return d

def spell_castable(s, c):
    """Lv 条件 + リーダー所持 (lr) を満たすか"""
    lr = POOL[c][6]
    if lr and not any(L['k'] == lr for L in s.leaders):
        return False
    return lv_ok(s, POOL[c][5])

class Side:
    def __init__(self, pair, is_first, ai_params=None):
        self.ai = ai_params or {}
        self.deck = build_deck(pair)
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
    return any(POOL[c][0]=='def' and POOL[c][3]==1 and spell_castable(s, c) for c in s.hand)

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
    extra = s.ai.get('awaken_min_P_extra', 0)
    if s.P < eff + extra: return
    s.P -= eff
    L['aw'] = True; L['awThis'] = True
    ab = LD[L['k']][5]
    if ab == 'oharai':
        if o.hand: o.trash.append(o.hand.pop(random.randrange(len(o.hand))))
        draw(s, 1)
    elif ab == 'charisma':
        # v3.4 スピア・ザ・グングニル: 相手のデッキを 4 枚トラッシュ
        mill(o, CFG.get('gungnir', 4))
    elif ab == 'four':
        # v3.4 レーヴァテイン: 相手デッキ-6 / 自デッキ-2 (v3.3 維持)
        mill(o, CFG.get('four_aw_mill', 6))
        mill(s, CFG.get('four_aw_self_mill', 2))

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
        if ab == 'koi': base += CFG.get('koi', 3)
        if ab == 'four': base += CFG.get('four', 5)
        # v3.4: マスタースパーク覚醒ターン = +6 (v3.3 維持)
        if ab == 'koi' and L['awThis']: base += CFG.get('koi_aw_bonus', 6)
        virt = 0
        if ab == 'oharai':
            virt = 3 if o.P > 0 else CFG.get('oharai_dmg', 0)
        if ab == 'charisma': virt = 2
        return base, virt, ab
    scored = [(leader_val(L), L) for L in s.leaders]
    scored.sort(key=lambda x: x[0][0]+x[0][1], reverse=True)
    (base, virt, ab), atkL = scored[0]
    reserve = s.ai.get('qdef_reserve', 2) if has_quick_def(s) else 0
    budget = max(0, s.P - reserve)
    spell_bonus = 0; direct = 0
    atk_cards = sorted([c for c in s.hand if POOL[c][0] in ('atk','mill') and spell_castable(s, c)],
                       key=lambda c: POOL[c][1], reverse=True)
    extra_self_mill = 0  # 攻撃時に追加で発動する自デッキ削り(マスタースパーク等)
    extra_opp_p_mill = 0  # 相手 P 追加削り(グングニル等)
    for c in atk_cards:
        k,val,pp,_,_,_,_ = POOL[c]
        if pp <= budget:
            budget -= pp
            s.hand.remove(c); s.trash.append(c)
            if k == 'atk': spell_bonus += val
            else: direct += val
            e = EXTRA.get(c, {})
            extra_self_mill += e.get('self_mill', 0)
            extra_opp_p_mill += e.get('opp_p_mill', 0)
    s.P = budget + reserve
    dL = best_def(o)
    da,de,_,_,dae,_ = LD[dL['k']]
    dval = dae if dL['aw'] else de
    raw = base + spell_bonus + (CFG.get('oharai_dmg', 0) if (ab == 'oharai' and o.P < 2) else 0)
    reduce = 0
    quick = sorted([c for c in o.hand if POOL[c][0]=='def' and POOL[c][3]==1 and spell_castable(o, c)],
                   key=lambda c: POOL[c][1], reverse=True)
    incoming = max(1, raw - dval)
    qdef_thresh = o.ai.get('qdef_threshold', 12)
    if quick and incoming > qdef_thresh and POOL[quick[0]][2] <= o.P:
        c = quick[0]
        o.P -= POOL[c][2]; o.hand.remove(c); o.trash.append(c)
        reduce += POOL[c][1]
    incoming = max(1, raw - dval - reduce)
    bomb_life = o.ai.get('bomb_life_threshold', 1)
    bomb_ratio = o.ai.get('bomb_deck_ratio', 1.0)
    use_bomb = o.bomb >= 2 and incoming >= bomb_ratio * len(o.deck) and o.life <= bomb_life
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
        # v3.4 フォーオブアカインド: 攻撃時 自デッキ-2 (v3.3 維持)
        mill(s, 2)
    elif ab == 'oharai':
        # 夢想封印: 相手 P -2(攻撃時に常時発動)
        o.P = max(0, o.P - 2)
    elif ab == 'charisma':
        # 吸血: トラッシュから 1 P 回収
        if s.trash: s.P += 1
    # 専用スペル追加効果(EXTRA で定義した self_mill / opp_p_mill)
    if extra_self_mill > 0:
        mill(s, extra_self_mill)
    if extra_opp_p_mill > 0:
        o.P = max(0, o.P - extra_opp_p_mill)
    atkL['rested'] = True
    for c in list(s.hand):
        k,val,pp,_,_,lv,_ = POOL[c]
        if k=='util' and pp<=s.P and spell_castable(s, c):
            s.P -= pp; s.hand.remove(c); s.trash.append(c); draw(s, max(1,val)); break
    while len(s.hand) > 7:
        s.trash.append(s.hand.pop())

def play(pa, pb, n_turns=80, ai_a=None, ai_b=None):
    A = Side(pa, True, ai_a); B = Side(pb, False, ai_b)
    cur, opp = A, B
    turns_played = 0
    for _ in range(n_turns):
        take_turn(cur, opp)
        turns_played += 1
        if opp.dead: return ('A' if cur is A else 'B'), turns_played
        if cur.dead: return ('B' if cur is A else 'A'), turns_played
        cur, opp = opp, cur
    if A.life != B.life:
        return ('A' if A.life > B.life else 'B'), turns_played
    return ('A' if len(A.deck)+len(A.trash) >= len(B.deck)+len(B.trash) else 'B'), turns_played

def run(games_per=2000):
    names = ['+'.join(p) for p in PAIRS]
    wins = {nm:0 for nm in names}; plays = {nm:0 for nm in names}
    fw = fg = 0
    matrix = {}
    total_turns = 0; total_games = 0
    for i, pa in enumerate(PAIRS):
        for j, pb in enumerate(PAIRS):
            if i == j: continue
            aw = 0
            for _ in range(games_per):
                r, t = play(pa, pb); fg += 1
                total_turns += t; total_games += 1
                if r == 'A':
                    aw += 1; wins[names[i]] += 1; fw += 1
                else:
                    wins[names[j]] += 1
                plays[names[i]] += 1; plays[names[j]] += 1
            matrix[(i,j)] = 100*aw/games_per
    rates = {nm: 100*wins[nm]/plays[nm] for nm in names}
    avg_turns = total_turns / total_games if total_games else 0
    return 100*fw/fg, rates, matrix, avg_turns

# ===== Stage A: 遺伝的アルゴリズム(GA)で AI 行動パラメータを進化 =====
def random_params():
    return {
        'qdef_reserve': random.randint(0, 3),
        'qdef_threshold': random.randint(6, 18),
        'bomb_life_threshold': random.randint(1, 3),
        'bomb_deck_ratio': round(random.uniform(0.6, 1.4), 2),
        'awaken_min_P_extra': random.randint(0, 2),
    }

def mutate(p, rate=0.35):
    p = dict(p)
    for k, v in list(p.items()):
        if random.random() < rate:
            if k == 'bomb_deck_ratio':
                p[k] = round(max(0.5, min(1.6, v + random.uniform(-0.25, 0.25))), 2)
            elif k == 'qdef_threshold':
                p[k] = max(4, min(22, v + random.randint(-3, 3)))
            elif k == 'qdef_reserve':
                p[k] = max(0, min(4, v + random.randint(-1, 1)))
            elif k == 'bomb_life_threshold':
                p[k] = max(1, min(3, v + random.randint(-1, 1)))
            elif k == 'awaken_min_P_extra':
                p[k] = max(0, min(3, v + random.randint(-1, 1)))
    return p

def crossover(a, b):
    return {k: (a[k] if random.random() < 0.5 else b[k]) for k in a}

def evolve_ai(generations=20, pop_size=14, games_per_indiv=120, seed=20260524):
    random.seed(seed)
    pop = [random_params() for _ in range(pop_size)]
    history = []
    for gen in range(generations):
        wins = [0] * pop_size
        for g in range(games_per_indiv):
            for i in range(pop_size):
                opps = [x for x in range(pop_size) if x != i]
                j = random.choice(opps)
                pa = random.choice(PAIRS)
                pb = random.choice([p for p in PAIRS if p != pa])
                # 半分は i が先攻、半分は j が先攻 ── 先攻有利を均す
                if g % 2 == 0:
                    r, _ = play(pa, pb, ai_a=pop[i], ai_b=pop[j])
                    if r == 'A': wins[i] += 1
                else:
                    r, _ = play(pb, pa, ai_a=pop[j], ai_b=pop[i])
                    if r == 'B': wins[i] += 1
        # 順位付け
        order = sorted(range(pop_size), key=lambda i: -wins[i])
        best_idx = order[0]
        best_fit = wins[best_idx]
        avg_fit = sum(wins) / pop_size
        history.append({
            'gen': gen,
            'best': best_fit,
            'avg': round(avg_fit, 1),
            'best_params': dict(pop[best_idx]),
            'max_possible': games_per_indiv,
        })
        # 上位半分が生存
        top = [pop[i] for i in order[:pop_size // 2]]
        # 残りは crossover + mutate
        new_pop = list(top)
        while len(new_pop) < pop_size:
            a, b = random.sample(top, 2)
            new_pop.append(mutate(crossover(a, b), rate=0.35))
        pop = new_pop
    return history, pop[0]

if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'balance'

    if mode == 'evolve':
        # GA で AI 行動パラメータを進化させる
        print("=== Stage A: 遺伝的アルゴリズムで AI を進化 ===")
        print("世代数 20 / 人口 14 / 1個体あたり 120 試合 = ~16800戦")
        history, best = evolve_ai(generations=20, pop_size=14, games_per_indiv=120)
        print()
        print("世代  最高勝点  平均勝点(120戦中)  最強パラメータ")
        for h in history:
            mp = h['max_possible']
            print("  %2d   %3d (%.0f%%)  %5.1f (%.0f%%)   %s" %
                  (h['gen'], h['best'], 100*h['best']/mp, h['avg'], 100*h['avg']/mp, h['best_params']))
        print()
        print("=== 最終最強パラメータ ===")
        for k, v in best.items():
            print("  %-22s = %s" % (k, v))
        print()
        # デフォルト AI(従来の貪欲)vs 進化済 AI 100戦
        DEFAULT_AI = {'qdef_reserve':2,'qdef_threshold':12,'bomb_life_threshold':1,'bomb_deck_ratio':1.0,'awaken_min_P_extra':0}
        random.seed(99)
        wins = 0; total = 200
        for g in range(total):
            pa = random.choice(PAIRS); pb = random.choice([p for p in PAIRS if p != pa])
            if g % 2 == 0:
                r, _ = play(pa, pb, ai_a=best, ai_b=DEFAULT_AI)
                if r == 'A': wins += 1
            else:
                r, _ = play(pb, pa, ai_a=DEFAULT_AI, ai_b=best)
                if r == 'B': wins += 1
        print("進化済 AI vs 従来 AI の対戦 %d戦: 進化 %d勝 / %.1f%%" % (total, wins, 100*wins/total))
    else:
        # 通常のバランス検証(v1.5 構成)
        random.seed(20260524)
        first, rates, matrix, avg_turns = run(3000)
        print("=== v1.5 (deck60) ペア別 総合勝率 (各 3000 戦/マッチ) ===")
        for nm in sorted(rates, key=lambda n: -rates[n]):
            print("  %-16s %.1f%%" % (nm, rates[nm]))
        sp = max(rates.values()) - min(rates.values())
        print("  ペア勝率幅 %.1fpt / 先攻勝率 %.1f%% / 平均 %.1f ターン" % (sp, first, avg_turns))
