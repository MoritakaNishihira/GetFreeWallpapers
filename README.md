# GetFreeWallpapers

Unsplash APIを使用した無料壁紙自動収集ツール

## 🌟 特徴

- **無料で高品質な壁紙を自動収集**
- **テーマ別の検索・ダウンロード**
- **JSON設定ファイルで簡単なテーマ管理**
- **重複ダウンロードの自動回避**
- **撮影者情報などのメタデータ保存**
- **Windows batファイルで簡単実行**

## 📋 必要な環境

- **Python 3.6以上**
- **インターネット接続**
- **Unsplash API キー**（無料取得可能）

## 🚀 セットアップ

### 1. ファイルのダウンロード

以下のファイルを同じフォルダに配置してください：

```
GetFreeWallpapers/
├── get_free_wallpapers.py      # メインスクリプト
├── get_free_wallpapers.bat     # Windows実行用
├── edit_themes.bat            # 設定編集用
└── README.md                  # このファイル
```

### 2. Unsplash API キーの取得

1. [Unsplash Developers](https://unsplash.com/developers) にアクセス
2. アカウント作成（無料）
3. 「New Application」でアプリケーションを作成
4. 「Access Key」をコピー

### 3. API キーの設定

`get_free_wallpapers.py`を開き、以下の行を編集：

```python
API_KEY = "YOUR_API_KEY_HERE"  # ← ここに取得したAccess Keyを貼り付け
```

### 4. 必要なライブラリのインストール

**自動インストール（推奨）：**
- `get_free_wallpapers.bat`を実行すると自動でインストールされます

**手動インストール：**
```bash
pip install requests
```

## 💻 使い方

### Windows（簡単）

1. **初回実行：** `get_free_wallpapers.bat`をダブルクリック
2. **設定編集：** `edit_themes.bat`をダブルクリック
3. **壁紙収集：** `get_free_wallpapers.bat`をダブルクリック

### コマンドライン

```bash
python get_free_wallpapers.py
```

## ⚙️ 設定ファイル（themes.json）

初回実行時に自動作成されるJSON設定ファイル：

```json
{
  "settings": {
    "count_per_theme": 5,           // 各テーマの取得枚数
    "resolution": "regular",        // 画質設定
    "orientation": "landscape"      // 画像の向き
  },
  "themes": [
    {
      "name": "自然風景",             // テーマ名
      "query": "nature landscape",   // 検索キーワード
      "enabled": true                // 有効/無効
    },
    {
      "name": "ミニマルデザイン",
      "query": "minimal abstract",
      "enabled": true
    },
    {
      "name": "都市建築",
      "query": "city architecture", 
      "enabled": false
    }
  ]
}
```

### 設定項目の説明

**settings:**
- `count_per_theme`: 各テーマで取得する壁紙枚数（1-30）
- `resolution`: 画質設定
  - `"thumb"` - サムネイル（200px程度）
  - `"small"` - 小サイズ（400px程度）
  - `"regular"` - 通常サイズ（1080p程度）**【推奨】**
  - `"full"` - フルサイズ（元解像度）
- `orientation`: 画像の向き
  - `"landscape"` - 横向き **【推奨】**
  - `"portrait"` - 縦向き
  - `"squarish"` - 正方形に近い

**themes:**
- `name`: テーマの表示名（日本語OK）
- `query`: Unsplashで検索するキーワード（英語推奨）
- `enabled`: そのテーマを有効にするかどうか

### 検索キーワードの例

| テーマ | おすすめキーワード |
|--------|-------------|
| 自然風景 | `nature landscape`, `mountain forest`, `ocean beach` |
| 都市・建築 | `city architecture`, `urban skyline`, `modern building` |
| 抽象・アート | `abstract art`, `geometric pattern`, `colorful design` |
| ミニマル | `minimal clean`, `simple design`, `white background` |
| 宇宙・科学 | `space galaxy`, `astronomy stars`, `science technology` |
| 動物 | `wildlife animals`, `cute pets`, `birds nature` |
| 食べ物 | `food photography`, `coffee aesthetic`, `healthy meal` |

## 📂 保存場所

壁紙は以下の場所に保存されます：
```
C:\Users\[ユーザー名]\Downloads\gfp\
```

各画像には以下のファイルが生成されます：
- `画像ID_撮影者名_説明.jpg` - 壁紙画像
- `画像ID_撮影者名_説明_metadata.json` - メタデータ（撮影者情報、ライセンス等）

## 🔧 トラブルシューティング

### よくある問題と解決方法

**❌ "Pythonがインストールされていません"**
- [Python公式サイト](https://python.org)からPythonをダウンロード・インストール
- インストール時に「Add Python to PATH」にチェック

**❌ "APIキーが設定されていません"**
- `get_free_wallpapers.py`内の`API_KEY`を実際のキーに変更

**❌ "検索エラー" / "401 Unauthorized"**
- APIキーが間違っている可能性があります
- Unsplash Developersで正しいAccess Keyを確認

**❌ "Rate limit exceeded"**
- 1時間に50回のAPI制限に達しました
- しばらく待ってから再実行してください

**❌ "themes.jsonの形式が正しくありません"**
- JSONファイルの構文エラーです
- ファイルを削除して再実行すると初期化されます

## 📊 API制限について

**無料プラン（Demo status）:**
- 1時間あたり50リクエスト
- 1日最大1,200枚の画像取得可能
- 個人利用・テスト用途には十分

**制限を確認する方法:**
- エラーメッセージでAPI制限に達したことが表示されます
- しばらく時間をおいてから再実行してください

## 📜 ライセンス

このツールはMITライセンスの下で公開されています。

**ダウンロードした壁紙について:**
- 全ての画像は[Unsplash License](https://unsplash.com/license)に従います
- 商用・非商用問わず自由に使用可能
- クレジット表記は不要（推奨）
- 各画像のメタデータに撮影者情報が保存されます

## 🤝 サポート

**バグ報告・機能要望:**
- GitHubのIssuesでお知らせください

**よくある質問:**
- READMEの「トラブルシューティング」を確認
- Unsplash APIの詳細は[公式ドキュメント](https://unsplash.com/documentation)を参照

## 🎨 カスタマイズのアイデア

- **季節テーマ**: 春夏秋冬の風景を定期収集
- **カラーテーマ**: 特定の色調（青系、暖色系等）で統一
- **用途別**: デスクトップ、スマホ、プレゼン資料用など
- **定期実行**: WindowsのタスクスケジューラでBatファイルを定期実行

---

**GetFreeWallpapers** - あなたのデスクトップを美しく彩る無料壁紙収集ツール 🌈