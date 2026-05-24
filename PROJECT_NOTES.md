# Touhou Card Forge — 東方カードゲーム制作ツール

## プロジェクト概要

「東方カードゲーム」(株式会社 Shangri-La 企画、2024 年 7 月仕様書)を題材にした自作 TCG 制作 Web アプリ。
手塚カードゲーム向けの `card-forge` をフォークして東方版に作り替え、現在は **v3.3(2リーダー制・デッキ60)** で運用。

- **メインファイル:** `index.html`(1 ファイル完結)
- **公開:** GitHub Pages 予定(リモート未設定)
- **フォーク元:** [fugaku-kobo/card-forge](https://github.com/fugaku-kobo/card-forge)(手塚版)
- **使用技術:** HTML + CSS + JavaScript(バニラ)、jsPDF、html2canvas、SheetJS(xlsx)、PeerJS

---

## 現在の状態(2026-05-24 / v3.3)

| 区分 | 内容 | 状態 |
|---|---|---|
| ルール | `docs/rules.md` v3.3(2リーダー制・行動済み・デッキ60・×0.75 スケール) | ✅ |
| カード設計 | `docs/cards.md` v1.5(リーダー4体・スペル24種・スターター2種・60枚) | ✅ |
| カード制作 / デッキ構築タブ | キャラ / スペルの 2 タイプ対応・エンジン用フィールド(engineKind/engineValue/bomCost) | ✅ |
| PLAY タブ | 2リーダー制・覚醒・行動済み・バトル(攻撃力−回避力)・リフレッシュ・BOM 詠唱 | ✅ |
| AI 対戦タブ | Greedy / MCTS / BOM 詠唱対応(`AIB_*` 内蔵カードプール) | ✅ |
| balance_sim.py | v1.5 同期、GA 進化モード(`python balance_sim.py evolve`) | ✅ |
| Excel インポート | 東方フォーマット | ✅ |
| ネット対戦同期 | 2リーダー版への追従 | ⏸ 未着手 |

---

## ゲーム仕様サマリ(詳細は `docs/rules.md`)

- **カードタイプ 2 種:** キャラ(リーダー)/ スペル
- **リーダー:** 試合前に 2 体選択。覚醒モデル(通常↔覚醒で攻撃/回避が切替)。攻撃したリーダーは「**行動済み**」になり、次の自分のターンまで迎撃に使えない
- **デッキ:** 60 枚(全スペル)、同 ID 上限 4
- **ゾーン(7 種):** デッキ / 手札(初期 4)/ リーダー(2 体)/ トラッシュ / P / ライフ(3)/ BOMB(3 固定)
- **コアループ:** 攻撃 = 相手デッキを削る(削り量 = max(1, 攻撃力 − 回避力))。デッキ 0 でリフレッシュ → ライフ −1。ライフ 0 で敗北
- **ターン(6 フェイズ):** ドロー → チャージ → 覚醒 → メイン → バトル → エンド
- **スペル詠唱:** PP コストの代替として **BOMB でも詠唱可能**(§G.5。1 枚につき PP か BOMB か排他選択)
- **試合時間:** 約 15〜20 分

### 用語
「没」は使わず **「トラッシュ」** で統一。

---

## ディレクトリ構成

```
touhou-card-forge/
├── index.html              # 単一ファイル本体
├── PROJECT_NOTES.md        # 本書
├── docs/
│   ├── rules.md            # ルール仕様(v3.1)
│   ├── cards.md            # カードリスト(リーダー4体・スペル24種・スターター2種)
│   ├── card_specs.md       # カードフィールド定義
│   └── legacy/             # フォーク元(手塚版)の旧 docs、12 TCG 研究を含む
```

---

## 開発環境

- **OS**: Windows / **エディタ**: VS Code + Git
- **ローカルプレビュー**: `python -m http.server 8765` → http://localhost:8765/index.html
- **ハードリロード**: `Ctrl+Shift+R`

## localStorage キー

- **東方版**: `touhou_card_forge_v1`
- 手塚版 `card_forge_data_v4_tezuka` からはマイグレーションしない(別ゲーム扱い)

---

## 既知の残課題

- **ネット対戦(PeerJS)** は v3.3 の 2リーダー / 覚醒 / 行動済み / BOM 詠唱に未追従(`netApplyRemoteOp` に attack/awaken/rested/flip/bomCast ハンドラが無い)
- **プレイ用デッキ** は「キャラ 2 枚 + スペル」で組む必要あり(開始時に場へ自動抽出)。デッキ外でリーダーを選ぶ専用 UI は未実装
- `index.html` に手塚版由来の死にコードが一部残存(dondeng 関連スタブ等。動作には無害)
- バランスは v3.3 で先攻 52.0% / ペア勝率幅 15.0pt(`balance_sim.py` 1000戦)。許容範囲だが、最強ペア(レミリア+フランドール 59%)と最弱ペア(霊夢+魔理沙 44%)の差を縮められる余地あり

---

## 関連ドキュメント

- `docs/rules.md` — 確定ルール(v3.3・2リーダー制・デッキ60)
- `docs/cards.md` — カード設計(リーダー4体・スペル24種・スターター2種・v1.5)
- `docs/card_specs.md` — カードデータ仕様(v3.3)
- `balance_sim.py` — 自動対戦シミュレーター(v1.5)。`python balance_sim.py` で 1000戦/ペア、`python balance_sim.py evolve` で GA 進化
- `docs/legacy/` — 手塚版アーカイブ(12 TCG 研究・プレイテスト資料)
