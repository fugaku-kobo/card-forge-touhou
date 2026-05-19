# Touhou Card Forge — 東方カードゲーム制作ツール

## プロジェクト概要

「東方カードゲーム」(株式会社 Shangri-La 企画、2024 年 7 月仕様書)を題材にした自作 TCG 制作 Web アプリ。
**手塚カードゲーム向けの `card-forge` をフォークして** 東方版に作り替え中。

- **メインファイル:** `index.html`(1 ファイル完結)
- **公開:** GitHub Pages 予定(リモート未設定)
- **フォーク元:** [fugaku-kobo/card-forge](https://github.com/fugaku-kobo/card-forge)(手塚版)
- **使用技術:** HTML + CSS + JavaScript(バニラ)、jsPDF、html2canvas、SheetJS(xlsx)、PeerJS(二台対戦の WebRTC)

---

## 現在の状態(2026-05-19)

| Phase | 内容 | 状態 |
|---|---|---|
| 0 | 計画・ルール把握(PDF + xlsx) | ✅ |
| 1 | docs 整備(legacy 退避+東方版 docs 新規) | ✅ |
| 2 | カードデータ構造の入れ替え(`BUILTIN_TYPES`/`STORAGE_KEY`) | ✅ |
| 3 | カード制作フォーム+`buildCardHTML`+ **東方テーマ**(夜空/朱/金) | ✅ |
| 4 | デッキ構築タブクリーンアップ(50 枚目安・主人公/別山ナシ) | ✅ |
| 5a | PLAY タブ データ構造(ライフ3/BOMB3/盤面1/手札4/P/トラッシュ) | ✅ |
| 5b | PLAY タブ UI 描画(東方ゾーン構造、覚醒バッジ等) | ✅ |
| 5c | Excel インポート(東方フォーマット) | ✅ |
| 6 | バトル/デッキリフレッシュ処理(攻撃力−回避力・回収P・BOMB無効化) | ✅ |
| 7 | ネット対戦同期更新(host/guest 初期化を東方版に) | ⏸ 未着手 |

主要な変更点(累積):
- カードタイプ: 3 種(キャラ/スペル/シューティング)
- localStorage キー: `touhou_card_forge_v1`
- カードモデル: 覚醒モデル(1 枚で通常↔覚醒の 2 状態)
- PLAY ゾーン: デッキ・手札・盤面1・トラッシュ・P・ライフ3・BOMB3
- バトル: 攻撃 → 攻撃力−回避力 = 相手デッキ削り、回収P 自動集計、デッキ0 でリフレッシュ
- 用語: 「没」→「トラッシュ」統一
- テーマ: 夜空の博麗神社(濃紺 + 朱赤 + 金)

---

## ゲーム仕様サマリ(詳細は `docs/rules.md`)

### カードタイプ(2 種)
- **キャラカード**: 盤面に 1 体、進化あり、攻撃力・回避力(進化で変動)
- **スペルカード**: 魔法相当、発動条件 Lv あり、P/BOMB コスト、バトル中も割り込み可

### ゾーン(8 種)
デッキ(50) / 手札(初期 4) / 盤面(1 体) / トラッシュ / P ゾーン / ライフ(3 裏) / BOMB(3 裏・固定) / 進化ゾーン

### コアループ
攻撃 = **相手デッキを削る**(攻撃力 − 回避力 = 削り枚数)。デッキ 0 でリフレッシュ→ライフ −1。ライフ 0 で敗北。
HP 削り合いではない **弾幕モデル**。

### ターン(6 フェイズ)
1. ドロー → 2. チャージ → 3. 進化 → 4. メイン → 5. バトル → 6. エンド

### 用語
「没」は使わず **「トラッシュ」** で統一。

---

## ディレクトリ構成

```
touhou-card-forge/
├── index.html              # 単一ファイル本体(手塚版のまま、Phase 2 以降書き換え)
├── PROJECT_NOTES.md        # 本書
├── docs/
│   ├── rules.md            # 東方版ルール仕様(現行)
│   ├── card_specs.md       # カードフィールド定義
│   └── legacy/             # フォーク元(手塚版)の旧 docs、参照用
│       ├── rule_status.md
│       ├── game_design.md
│       ├── draft_rules_v4.md
│       ├── tcg_research.md
│       └── playtest_demos.md
└── .tmp/                   # 一時スクリプト(gitignore)
```

---

## 開発環境

- **OS**: Windows
- **エディタ**: VS Code + Git
- **ローカルパス**: `C:\Users\fd557\projects\touhou-card-forge\`
- **ローカルプレビュー**: `python -m http.server 8765` → http://localhost:8765/index.html
  - `file://` でも開けるが、PeerJS や一部 API のため localhost 推奨
- **ハードリロード**: `Ctrl+Shift+R`

---

## localStorage キー

- **東方版**: `touhou_card_forge_v1`(Phase 2 で導入)
- **手塚版**: `card_forge_data_v4_tezuka`(マイグレーションせず、ブラウザに残るが無視)

---

## 旧手塚版のコードマップ(参考)

`index.html` 内の主要関数(現状は手塚版そのまま、Phase 2-6 で大半が書き換え対象):

- `buildCardHTML(c, idx, opts)` — カード描画(タイプ別レイアウト)
- `buildCardChip(inst, side, fromZone, faceDown)` — プレイマット用 63×88px チップ
- `importXLSX(ev)` — Excel 読み込み
- `generatePDF(mode)` — PDF 生成
- `renderPlay()` / `renderPlaySide()` / `renderTurnBar()` — PLAY タブ描画
- `startPlaySession()` / `endTurn()` / `moveInstance()` — プレイ進行
- `showPlayHoverPreview()` — ホバー原寸プレビュー

詳細は `docs/legacy/rule_status.md` および旧 PROJECT_NOTES のスナップショット
(git log を `05fb368^` まで遡れば手塚版そのまま)を参照。

---

## 関連ドキュメント

- `docs/rules.md` — 確定ルール
- `docs/card_specs.md` — カードデータ仕様
- `docs/legacy/` — 手塚版アーカイブ
