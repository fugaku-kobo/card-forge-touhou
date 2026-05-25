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
 ('disrupt', 2, 3, 0, 0, 1, '霊夢'),  # TH-104 神技『八方鬼縛陣』 (v1.7 では P-2)
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
 # ===== v1.8 カウンター 6 種 (TH-501..506) — 手札から相手ターン中に発動 =====
 ('def',     0, 4, 1, 0, 1, '霊夢'),       # TH-501 結界『博麗弾結界』(完全無効)
 ('def',     0, 3, 1, 0, 2, '霊夢'),       # TH-502 神技『陰陽弾』(覚醒打消し)
 ('disrupt', 0, 3, 1, 0, 1, '魔理沙'),     # TH-503 魔符『閃光』(詠唱無効)
 ('def',     0, 3, 1, 0, 1, 'レミリア'),   # TH-504 紅符『緋色の波』(半減+反射)
 ('disrupt', 0, 4, 1, 0, 2, 'フラン'),     # TH-505 禁弾『刻時停止』(覚醒リーダー凍結)
 ('disrupt', 0, 2, 1, 0, 1, ''),           # TH-506 結界『縛』(追加コスト要求)
]
# v1.8: カウンタースペルの triggerTiming(POOL の index → 発動可能タイミング)
TRIGGER = {
    30: 'opp_atk_declare',  # TH-501 博麗弾結界
    31: 'opp_awaken',       # TH-502 陰陽弾
    32: 'opp_cast',         # TH-503 閃光
    33: 'opp_atk_declare',  # TH-504 緋色の波
    34: 'opp_awaken',       # TH-505 刻時停止
    35: 'opp_cast',         # TH-506 縛
}
# v1.7: ex 効果辞書 (index.html の AIB_POOL.ex と同期)
# 攻撃系: self_mill, opp_p_mill, bonus_if_opp_p_low{th,v}, bonus_if_low_life,
#         bonus_if_high_trash{th,v}, bonus_if_low_deck{th,v}, bonus_if_opp_awakened,
#         draw_on_hit, bomb_on_hit
# 防御系: negate_if_low_life, negate_if_opp_multi_spell{n}, counter_mill, counter_p_mill,
#         bomb_on_defend, draw_on_defend, next_atk_bonus
EXTRA = {
    # 共有
    1:  {'bonus_if_opp_p_low': {'th':2,'v':3}},       # TH-002 アグニシャイン
    2:  {'draw_on_hit': 1},                            # TH-003 サイレントセレナ
    3:  {'draw_on_defend': 1},                         # TH-004 生死の境界
    4:  {'bomb_on_defend': 1},                         # TH-005 弾幕結界
    5:  {'negate_if_opp_multi_spell': {'n':2}, 'next_atk_bonus': 4},  # TH-006 大結界
    # 霊夢専用
    10: {'opp_p_mill': 1, 'bonus_if_opp_p_low': {'th':0,'v':4}},  # TH-101 博麗符印
    11: {'draw_on_hit': 1},                            # TH-102 夢想封印 集
    12: {'counter_mill': 3, 'draw_on_defend': 1},      # TH-103 博麗結界
    13: {'opp_p_mill': 2},                             # TH-104 八方鬼縛陣 (disrupt の val=2 と二重で適用しない: val を 2 にしてここは無し)
    14: {'negate_if_low_life': 1, 'counter_p_mill': 2}, # TH-105 楽園
    # 魔理沙専用
    15: {'bonus_if_high_trash': {'th':8,'v':3}},       # TH-201 マスタースパーク
    16: {'self_mill': 2, 'bonus_if_high_trash': {'th':12,'v':4}},  # TH-202 ファイナル
    17: {'draw_on_hit': 1},                            # TH-203 ドラゴンメテオ
    # レミリア専用
    20: {'bomb_on_hit': 1},                            # TH-301 スカーレットシュート
    21: {'opp_p_mill': 2, 'bonus_if_opp_awakened': 3}, # TH-302 グングニル
    22: {'bonus_if_opp_awakened': 2},                  # TH-303 スカーレットデビル
    24: {'counter_p_mill': 2},                         # TH-305 永遠に紅い幼き月
    # フランドール専用
    25: {'self_mill': 1, 'bonus_if_low_deck': {'th':25,'v':5}},  # TH-401 フォーオブ
    27: {'opp_p_mill': 2},                             # TH-403 カゴメカゴメ
    28: {'bonus_if_low_life': 5},                      # TH-404 スターボウ
    29: {'bomb_on_hit': 1, 'bonus_if_low_life': 8},    # TH-405 悪魔の妹
    # v1.8 カウンター ex
    30: {'negate_attack': 1},                          # TH-501 博麗弾結界
    31: {'negate_awaken_effect': 1},                   # TH-502 陰陽弾
    32: {'negate_spell': 1},                           # TH-503 閃光
    33: {'half_attack': 1, 'reflect_to_opp': 1},       # TH-504 緋色の波
    34: {'freeze_awakened_leader': 1},                 # TH-505 刻時停止
    35: {'spell_cost_surcharge': 1},                   # TH-506 縛
}
# TH-104 八方鬼縛陣の POOL val (=2) は disrupt として独立して相手 P -2、EXTRA 13 と二重発動しないよう注意

# ペア → 該当リーダー名
LEADER_OF_PAIR = {pair: [pair[0], pair[1]] for pair in [('魔理沙','フラン'), ('魔理沙','レミリア'), ('霊夢','フラン'), ('霊夢','魔理沙'), ('レミリア','フラン'), ('霊夢','レミリア')]}

def usable_indices(pair):
    """このペアで使用可能なカードインデックス(共有+両リーダー専用) = 20種"""
    return [i for i, c in enumerate(POOL) if c[6]=='' or c[6] in pair]

def build_deck(pair):
    """v1.8 スターター: カウンターは少なめに分配(共有2枚/専用1枚)で計65枚前後"""
    d = []
    for i in usable_indices(pair):
        is_counter = i in TRIGGER
        if POOL[i][6] == '':  # 共有
            n = 4 if not is_counter else 2
        else:  # 専用
            n = 2 if not is_counter else 1
        d += [i] * n
    random.shuffle(d)
    return d

def spell_castable(s, c):
    """Lv 条件 + リーダー所持 (lr) を満たすか"""
    lr = POOL[c][6]
    if lr and not any(L['k'] == lr for L in s.leaders):
        return False
    return lv_ok(s, POOL[c][5])

def check_counter(reactor, actor, timing, ctx=None):
    """v1.8: 相手の手札からカウンタースペルを発動するか判断し、効果 dict を返す"""
    candidates = [c for c in reactor.hand
        if TRIGGER.get(c) == timing
        and spell_castable(reactor, c)
        and POOL[c][2] <= reactor.P]
    if not candidates: return None
    # 簡単な heuristic で選択
    for c in candidates:
        ex = EXTRA.get(c, {})
        if 'negate_attack' in ex and ctx and ctx.get('atk_raw', 0) >= 14: pick = c; break
        if 'half_attack' in ex and ctx and ctx.get('atk_raw', 0) >= 12: pick = c; break
        if 'negate_spell' in ex and ctx and ctx.get('spell_v', 0) >= 8: pick = c; break
        if 'spell_cost_surcharge' in ex and ctx and actor.P < ctx.get('spell_pp', 0) + 1: pick = c; break
        if 'negate_awaken_effect' in ex: pick = c; break
        if 'freeze_awakened_leader' in ex: pick = c; break
    else:
        return None
    reactor.P -= POOL[pick][2]
    reactor.hand.remove(pick)
    reactor.trash.append(pick)
    return EXTRA.get(pick, {})

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
        # v3.7: awakenGauge / awakenedTurn / awakenedAttackCount を導入
        self.leaders = [{'k':k,'aw':False,'rested':False,'awThis':False,
                         'awakenGauge':0,'awakenedTurn':None,'awakenedAttackCount':0} for k in pair]

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

def progress_gauge(s, o, idx):
    """v3.7: ゲージ +1。3 到達で自動覚醒。"""
    L = s.leaders[idx]
    if L['awakenGauge'] >= 3: return False
    L['awakenGauge'] += 1
    if L['awakenGauge'] >= 3:
        awaken_leader(s, o, L)
    return True

def choose_main_action(s, o):
    """v3.7: 'attack' / 'gauge:N' / 'wait' を返す"""
    unawakened = next((i for i,L in enumerate(s.leaders) if L['awakenGauge']<3), -1)
    if unawakened < 0: return 'attack'
    if s.turncount <= 2: return 'attack'
    if o.life < s.life: return 'attack'  # 自分有利、押し切り
    if o.life == s.life:
        opp_max = max(L['awakenGauge'] for L in o.leaders)
        my_max = max(L['awakenGauge'] for L in s.leaders)
        if opp_max > my_max: return 'gauge:%d' % unawakened
        return 'gauge:%d' % unawakened if s.turncount % 4 == 0 else 'attack'
    return 'gauge:%d' % unawakened

def awaken_leader(s, o, L):
    """v3.7: 旧 covenant の覚醒スキル発動部分を抜き出した関数。PP コストなし。"""
    L['aw'] = True; L['awThis'] = True
    L['awakenedTurn'] = s.turncount
    L['awakenedAttackCount'] = 0
    ab = LD[L['k']][5]
    if ab == 'oharai':
        if o.hand: o.trash.append(o.hand.pop(random.randrange(len(o.hand))))
        draw(s, 1)
    elif ab == 'charisma':
        # v3.4 スピア・ザ・グングニル: 相手のデッキを 4 枚トラッシュ
        mill(o, CFG.get('gungnir', 4))
    elif ab == 'four':
        # v3.4 レーヴァテイン: 相手デッキ-6 / 自デッキ-1 (代償軽減 2→1)
        mill(o, CFG.get('four_aw_mill', 6))
        mill(s, CFG.get('four_aw_self_mill', 1))
    # v1.8: 相手のカウンターチェック (opp_awaken)
    cnt = check_counter(o, s, 'opp_awaken')
    if cnt:
        if cnt.get('negate_awaken_effect'):
            pass  # 効果は既に発動済み(簡略化のためここでは無効化できないが、覚醒コストは消費維持)
        if cnt.get('freeze_awakened_leader'):
            L['_frozen'] = True

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
        if L.get('_frozen'):
            L['rested'] = True; L['_frozen'] = False
        else:
            L['rested'] = False
        L['awThis'] = False
    # v3.7: 覚醒済みリーダーの「毎ターン開始時」継続効果
    for L in s.leaders:
        if L['awakenGauge'] < 3: continue
        ab = LD[L['k']][5]
        if ab == 'oharai':
            o.P = max(0, o.P - 1)  # 霊夢覚醒『無敵巫女』
        elif ab == 'charisma':
            if s.trash:
                s.P = min(7, s.P + 1)  # レミリア覚醒『紅夜の覇者』
    if not (s.is_first and s.turncount == 1):
        draw(s, 1)
    if s.dead: return
    if s.hand:
        s.P = min(7, s.P + 1)
        order = sorted(range(len(s.hand)), key=lambda i: (POOL[s.hand[i]][0]!='util', POOL[s.hand[i]][1]))
        s.hand.pop(order[0])
        draw(s, 1)
        if s.dead: return
    # v3.7: メインフェーズ 3 択
    if s.turncount >= 2:
        action = choose_main_action(s, o)
        if action.startswith('gauge:'):
            idx = int(action.split(':')[1])
            progress_gauge(s, o, idx)
            if s.dead or o.dead: return
            return  # ゲージ進行ターンは攻撃しない
        elif action == 'wait':
            return
        # 'attack' は下の do_attack へ
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
        # v3.7: 覚醒継続効果
        if L['awakenGauge'] >= 3:
            if ab == 'koi':
                if L['awakenedAttackCount'] == 0:
                    base += 8  # マスタースパーク(覚醒後最初の攻撃)
                if len(s.trash) >= 12:
                    base += 4  # コレクション
            if ab == 'four':
                elapsed = max(0, s.turncount - (L['awakenedTurn'] or s.turncount))
                base += elapsed  # フラン覚醒経過ターン累積
        virt = 0
        # v1.7: お祓い弱化 (P-2→P-1) に合わせ virt 3→1
        if ab == 'oharai': virt = 1 if o.P > 0 else 0
        if ab == 'charisma': virt = 2
        return base, virt, ab
    scored = [(leader_val(L), L) for L in s.leaders]
    scored.sort(key=lambda x: x[0][0]+x[0][1], reverse=True)
    (base, virt, ab), atkL = scored[0]
    reserve = s.ai.get('qdef_reserve', 2) if has_quick_def(s) else 0
    budget = max(0, s.P - reserve)
    spell_bonus = 0; direct = 0
    # v3.7+: 専用スペルは攻撃リーダー固有(他リーダー攻撃には乗せない)
    atkL_name = atkL['k']
    atk_cards = sorted([c for c in s.hand if POOL[c][0] in ('atk','mill') and spell_castable(s, c)
                        and (not POOL[c][6] or POOL[c][6] == atkL_name)],
                       key=lambda c: POOL[c][1], reverse=True)
    cast_cards = []  # 詠唱した atk/mill カードの index リスト
    extra_self_mill = 0; extra_opp_p_mill = 0
    extra_draw_hit = 0; extra_bomb_hit = 0
    ex_bonus = 0  # v1.7: bonus_if_* の合計
    for c in atk_cards:
        k,val,pp,_,_,_,_ = POOL[c]
        if pp <= budget:
            budget -= pp
            s.hand.remove(c); s.trash.append(c); cast_cards.append(c)
            if k == 'atk': spell_bonus += val
            else: direct += val
            e = EXTRA.get(c, {})
            extra_self_mill += e.get('self_mill', 0)
            extra_opp_p_mill += e.get('opp_p_mill', 0)
            extra_draw_hit += e.get('draw_on_hit', 0)
            extra_bomb_hit += e.get('bomb_on_hit', 0)
            # v1.7 bonus_if_* 集計
            if 'bonus_if_opp_p_low' in e and o.P <= e['bonus_if_opp_p_low']['th']:
                ex_bonus += e['bonus_if_opp_p_low']['v']
            if 'bonus_if_low_life' in e and s.life <= 1:
                v = e['bonus_if_low_life']
                ex_bonus += v if isinstance(v, int) else v.get('v', 0)
            if 'bonus_if_high_trash' in e and len(s.trash) >= e['bonus_if_high_trash']['th']:
                ex_bonus += e['bonus_if_high_trash']['v']
            if 'bonus_if_low_deck' in e and len(s.deck) <= e['bonus_if_low_deck']['th']:
                ex_bonus += e['bonus_if_low_deck']['v']
            if 'bonus_if_opp_awakened' in e and any(L['aw'] for L in o.leaders):
                v = e['bonus_if_opp_awakened']
                ex_bonus += v if isinstance(v, int) else v.get('v', 0)
    # v1.7: 前ターンの next_atk_bonus を消費
    ex_bonus += s.__dict__.pop('_next_atk_bonus', 0)
    s.P = budget + reserve
    dL = best_def(o)
    da,de,_,_,dae,_ = LD[dL['k']]
    dval = dae if dL['aw'] else de
    raw = base + spell_bonus + ex_bonus
    # v1.8: 相手のカウンターチェック (opp_atk_declare)
    cntA = check_counter(o, s, 'opp_atk_declare', {'atk_raw': raw})
    if cntA:
        if cntA.get('negate_attack'):
            atkL['rested'] = True
            return  # 攻撃完全無効化
        if cntA.get('half_attack'):
            raw = (raw + 1) // 2  # 切り上げ
        # reflect_to_opp は最終 final 確定後に処理
    reduce = 0; def_card = None
    # v1.7: 防御カード選択 (negate_if_* を最優先)
    quick = sorted([c for c in o.hand if POOL[c][0]=='def' and POOL[c][3]==1 and spell_castable(o, c)],
                   key=lambda c: POOL[c][1], reverse=True)
    negate_card = None
    for c in quick:
        if POOL[c][2] > o.P: continue
        e = EXTRA.get(c, {})
        if e.get('negate_if_low_life') and o.life <= 1: negate_card = c; break
        if 'negate_if_opp_multi_spell' in e and len(cast_cards) >= e['negate_if_opp_multi_spell']['n']:
            negate_card = c; break
    qdef_thresh = o.ai.get('qdef_threshold', 12)
    incoming = max(1, raw - dval)
    if negate_card is not None:
        def_card = negate_card
        o.P -= POOL[negate_card][2]; o.hand.remove(negate_card); o.trash.append(negate_card)
    elif quick and incoming > qdef_thresh and POOL[quick[0]][2] <= o.P:
        c = quick[0]; def_card = c
        o.P -= POOL[c][2]; o.hand.remove(c); o.trash.append(c)
        reduce += POOL[c][1]
    incoming = max(1, raw - dval - reduce)
    bomb_life = o.ai.get('bomb_life_threshold', 1)
    bomb_ratio = o.ai.get('bomb_deck_ratio', 1.0)
    use_bomb = (negate_card is None) and o.bomb >= 2 and incoming >= bomb_ratio * len(o.deck) and o.life <= bomb_life
    if use_bomb: o.bomb -= 2
    negated = negate_card is not None
    final = 0 if (use_bomb or negated) else max(1, raw - dval - reduce)
    if CFG.get('first_t1_atk_half') and s.is_first and s.turncount == 1:
        final = max(1, final // 2)
    if final > 0:
        milled = mill(o, final)
        s.P = min(7, s.P + min(sum(POOL[c][4] for c in milled), 3))  # v1.7: PP 上限 7
    if direct > 0 and not o.dead:
        mill(o, direct)
    # v1.8: reflect_to_opp(カウンター緋色の波)— final 分を s.deck に反射
    if cntA and cntA.get('reflect_to_opp') and final > 0:
        mill(s, final)
    # v1.7: 攻撃命中時の ex
    if final > 0 and extra_draw_hit > 0:
        draw(s, extra_draw_hit)
    if final > 0 and extra_bomb_hit > 0:
        s.bomb = min(6, s.bomb + extra_bomb_hit)
    # v1.7: 防御スペル ex (counter/draw/bomb/next_atk_bonus)
    if def_card is not None and not use_bomb:
        de = EXTRA.get(def_card, {})
        if de.get('counter_mill', 0) > 0:
            mill(s, de['counter_mill'])
        if de.get('counter_p_mill', 0) > 0:
            s.P = max(0, s.P - de['counter_p_mill'])
        if de.get('draw_on_defend', 0) > 0:
            draw(o, de['draw_on_defend'])
        if de.get('bomb_on_defend', 0) > 0:
            o.bomb = min(6, o.bomb + de['bomb_on_defend'])
        if de.get('next_atk_bonus', 0) > 0:
            o._next_atk_bonus = getattr(o, '_next_atk_bonus', 0) + de['next_atk_bonus']
    if ab == 'four':
        # v3.4 フォーオブアカインド: 攻撃時 自デッキ-2 (v3.3 維持)
        mill(s, 2)
    elif ab == 'oharai':
        # v1.7: 無敵巫女(夢想妙珠): 相手 P -1(常時)に弱化
        o.P = max(0, o.P - 1)
    elif ab == 'charisma':
        # 吸血: トラッシュ 4 枚以上で 1 P 回収
        if len(s.trash) >= 4: s.P = min(7, s.P + 1)
    # 専用スペル追加効果(EXTRA で定義した self_mill / opp_p_mill)
    if extra_self_mill > 0:
        mill(s, extra_self_mill)
    if extra_opp_p_mill > 0:
        o.P = max(0, o.P - extra_opp_p_mill)
    atkL['rested'] = True
    # v3.7: 攻撃したリーダーが覚醒済みなら覚醒継続効果の副作用
    if atkL['awakenGauge'] >= 3:
        atkL['awakenedAttackCount'] += 1
        if ab == 'koi' and atkL['awakenedAttackCount'] == 1:
            mill(s, 2)  # マスタースパーク代償
        if ab == 'four':
            mill(s, 1)  # フラン覚醒の自デッキ累積
        if ab == 'charisma':
            target = sorted([L for L in o.leaders if 0 < L['awakenGauge'] < 3],
                            key=lambda L: -L['awakenGauge'])
            if target: target[0]['awakenGauge'] -= 1
    # v3.7: 防御側に霊夢覚醒済みがいて、final > 0 なら BOMB +1
    if final > 0:
        if any(L['awakenGauge']>=3 and LD[L['k']][5]=='oharai' for L in o.leaders):
            o.bomb = min(6, o.bomb + 1)
    for c in list(s.hand):
        k,val,pp,_,_,lv,_ = POOL[c]
        if k=='util' and pp<=s.P and spell_castable(s, c):
            # v1.8: opp_cast カウンターチェック
            cntC = check_counter(o, s, 'opp_cast', {'spell_v': val, 'spell_pp': pp})
            if cntC:
                if cntC.get('negate_spell'):
                    s.P -= pp; s.hand.remove(c); s.trash.append(c)
                    break  # 効果なしでコストだけ消費
                if cntC.get('spell_cost_surcharge'):
                    if s.P < pp + 1:
                        break  # 追加コスト払えず失敗
                    s.P -= 1
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
