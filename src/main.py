#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GetFreeWallpapers - Unsplash APIを使った無料壁紙自動収集ツール

機能:
- テーマ別の壁紙検索・ダウンロード
- JSON設定ファイルでのテーマ管理
- ダウンロードフォルダ内のgfpフォルダに保存
- SQLiteデータベースでメタデータ管理
- 既存画像をスキップして確実に指定枚数をダウンロード
"""

import requests
import os
import json
import time
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

class GetFreeWallpapers:
    def __init__(self, api_key):
        """
        GetFreeWallpapers - Unsplash壁紙収集ツール
        
        Args:
            api_key (str): Unsplash API キー
        """
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"
        self.headers = {"Authorization": f"Client-ID {api_key}"}
        
        # ダウンロードフォルダ内にgfpフォルダを作成
        downloads_folder = Path.home() / "Downloads"
        self.download_dir = downloads_folder / "gfp"
        
        # srcフォルダと同じ階層にデータベースファイルを作成
        current_dir = Path(__file__).parent  # src フォルダのパス
        project_root = current_dir.parent    # プロジェクトルートのパス
        self.db_path = project_root / "db/wallpapers.db"
        
        # ダウンロードディレクトリを作成
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        # データベースを初期化
        self.init_database()
    
    def init_database(self):
        """
        SQLiteデータベースとテーブルを初期化
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # wallpapers テーブルを作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wallpapers (
                    id TEXT PRIMARY KEY,
                    description TEXT,
                    photographer TEXT NOT NULL,
                    photographer_url TEXT,
                    unsplash_url TEXT NOT NULL,
                    download_date TEXT NOT NULL,
                    license TEXT DEFAULT 'Unsplash License',
                    tags TEXT,  -- JSON形式で保存
                    width INTEGER,
                    height INTEGER,
                    image_file TEXT NOT NULL,
                    theme_name TEXT,
                    theme_query TEXT,
                    file_size INTEGER,
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # インデックスを作成（検索パフォーマンス向上）
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_photographer ON wallpapers(photographer)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_theme_name ON wallpapers(theme_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_date ON wallpapers(download_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resolution ON wallpapers(resolution)')
            
            conn.commit()
            conn.close()
            print(f"✅ データベースを初期化しました: {self.db_path}")
            
        except Exception as e:
            print(f"❌ データベース初期化エラー: {e}")
    
    def search_wallpapers(self, theme, count=10, resolution="full", orientation="landscape", page=1):
        """
        テーマに基づいて壁紙を検索
        
        Args:
            theme (str): 検索テーマ（例: "nature", "city", "minimal"）
            count (int): 取得枚数（最大30）
            resolution (str): 画質 ("thumb", "small", "regular", "full", "raw")
            orientation (str): 向き ("landscape", "portrait", "squarish")
            page (int): ページ番号（1から開始）
            
        Returns:
            list: 画像データのリスト（フルHD以上の横長画像のみ）
        """
        url = f"{self.base_url}/search/photos"
        params = {
            "query": theme,
            "per_page": min(count, 30),  # 1ページあたり最大30件
            "orientation": orientation,
            "order_by": "relevant",
            "page": page
        }
        
        try:
            print(f"🔍 テーマ '{theme}' で検索中... (ページ {page})")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            all_photos = data.get("results", [])
            total_pages = data.get("total_pages", 1)
            
            # フルHD以上の横長画像のみをフィルタリング
            filtered_photos = []
            for photo in all_photos:
                width = photo.get("width", 0)
                height = photo.get("height", 0)
                
                # フルHD以上 (1920x1080) かつ横長 (アスペクト比 > 1.2) の画像のみ
                if width >= 1920 and height >= 1080 and (width / height) > 1.2:
                    filtered_photos.append(photo)
            
            print(f"✅ ページ{page}: {len(filtered_photos)}枚のフルHD以上横長画像が見つかりました (総ページ数: {total_pages})")
            return filtered_photos, total_pages
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 検索エラー: {e}")
            return [], 1
    
    def load_themes_config(self, config_file="ToolSettings.json"):
        """
        テーマ設定ファイルを読み込み
        
        Args:
            config_file (str): 設定ファイル名
            
        Returns:
            dict: テーマ設定
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 設定ファイル '{config_file}' を読み込みました")
            return config
        except FileNotFoundError:
            # デフォルト設定ファイルを作成
            default_config = {
                "settings": {
                    "count_per_theme": 5,
                    "resolution": "regular",
                    "orientation": "landscape"
                },
                "themes": [
                    {
                        "name": "自然風景",
                        "query": "nature landscape",
                        "enabled": True
                    },
                    {
                        "name": "ミニマルデザイン",
                        "query": "minimal abstract",
                        "enabled": True
                    },
                    {
                        "name": "都市建築",
                        "query": "city architecture",
                        "enabled": True
                    },
                    {
                        "name": "海の夕日",
                        "query": "ocean sunset",
                        "enabled": False
                    },
                    {
                        "name": "森と山",
                        "query": "forest mountains",
                        "enabled": False
                    }
                ]
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            
            print(f"📝 デフォルト設定ファイル '{config_file}' を作成しました")
            print(f"💡 設定を変更してから再実行してください")
            return default_config
        except json.JSONDecodeError as e:
            print(f"❌ 設定ファイルの形式が正しくありません: {e}")
            return None
    
    def is_already_downloaded(self, photo):
        """
        画像が既にダウンロード済みかを判定（SQLiteデータベースを確認）
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            
        Returns:
            tuple: (bool, str) - (既にダウンロード済みか, 既存ファイルパス)
        """
        photo_id = photo["id"]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 画像IDでデータベースを検索
            cursor.execute('SELECT image_file FROM wallpapers WHERE id = ?', (photo_id,))
            result = cursor.fetchone()
            
            if result:
                image_filename = result[0]
                image_path = self.download_dir / image_filename
                
                # 実際のファイルが存在するかチェック
                if image_path.exists():
                    conn.close()
                    return True, str(image_path)
                else:
                    # データベースにはあるがファイルが存在しない場合、レコードを削除
                    cursor.execute('DELETE FROM wallpapers WHERE id = ?', (photo_id,))
                    conn.commit()
                    print(f"🗑️  存在しない画像のレコードを削除: {photo_id}")
            
            conn.close()
            return False, None
            
        except Exception as e:
            print(f"❌ データベース確認エラー: {e}")
            return False, None
    
    def download_image(self, photo, resolution="full", theme_name="", theme_query=""):
        """
        画像をダウンロード
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            resolution (str): ダウンロード解像度
            theme_name (str): テーマ名
            theme_query (str): 検索クエリ
            
        Returns:
            str: ダウンロードしたファイルパス（失敗時はNone、既存時は"SKIPPED"）
        """
        try:
            # 既にダウンロード済みかチェック
            is_downloaded, existing_path = self.is_already_downloaded(photo)
            if is_downloaded:
                print(f"⏭️  スキップ: {os.path.basename(existing_path)} (ID: {photo['id']}) - 既存")
                return "SKIPPED"
            
            # 画像URLを取得
            image_url = photo["urls"].get(resolution)
            if not image_url:
                print(f"❌ {resolution}解像度が利用できません")
                return None
            
            # ファイル名を生成
            photo_id = photo["id"]
            photographer = photo["user"]["name"].replace(" ", "_")
            description = photo.get("alt_description", "wallpaper").replace(" ", "_")[:30]
            
            # ファイル拡張子を取得
            parsed_url = urlparse(image_url)
            ext = ".jpg"  # Unsplashは主にJPG形式
            
            filename = f"{photo_id}_{photographer}_{description}{ext}"
            # ファイル名から不正な文字を除去
            filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
            filepath = self.download_dir / filename
            
            # 画像をダウンロード
            print(f"⬇️  ダウンロード中: {filename} ({photo.get('width', '?')}x{photo.get('height', '?')})")
            img_response = requests.get(image_url)
            img_response.raise_for_status()
            
            # ファイルに保存
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            # ファイルサイズを取得
            file_size = filepath.stat().st_size
            
            # メタデータをデータベースに保存
            self.save_metadata_to_db(photo, str(filepath), theme_name, theme_query, file_size, resolution)
            
            print(f"✅ 完了: {filename}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ ダウンロードエラー: {e}")
            return None
    
    def save_metadata_to_db(self, photo, filepath, theme_name, theme_query, file_size, resolution):
        """
        画像のメタデータをSQLiteデータベースに保存
        
        Args:
            photo (dict): Unsplash APIから取得した画像データ
            filepath (str): 保存したファイルパス
            theme_name (str): テーマ名
            theme_query (str): 検索クエリ
            file_size (int): ファイルサイズ（バイト）
            resolution (str): ダウンロード解像度
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # タグをJSON文字列として準備
            tags_json = json.dumps([tag["title"] for tag in photo.get("tags", [])])
            
            # データを挿入
            cursor.execute('''
                INSERT OR REPLACE INTO wallpapers (
                    id, description, photographer, photographer_url, unsplash_url,
                    download_date, license, tags, width, height, image_file,
                    theme_name, theme_query, file_size, resolution
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                photo["id"],
                photo.get("alt_description"),
                photo["user"]["name"],
                photo["user"]["links"]["html"],
                photo["links"]["html"],
                datetime.now().isoformat(),
                "Unsplash License",
                tags_json,
                photo.get("width"),
                photo.get("height"),
                os.path.basename(filepath),
                theme_name,
                theme_query,
                file_size,
                resolution
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ データベース保存エラー: {e}")
    
    def collect_theme_wallpapers(self, theme_config, settings):
        """
        単一テーマで指定枚数の壁紙を確実に収集
        
        Args:
            theme_config (dict): テーマ設定
            settings (dict): 全体設定
            
        Returns:
            int: 新規ダウンロードした枚数
        """
        theme_name = theme_config.get("name", "不明")
        query = theme_config.get("query", "")
        target_count = settings.get("count_per_theme", 5)
        resolution = settings.get("resolution", "regular")
        orientation = settings.get("orientation", "landscape")
        
        print(f"🎨 テーマ: {theme_name} (検索: '{query}') - 目標: {target_count}枚")
        
        if not query:
            print(f"⚠️  スキップ: 検索クエリが設定されていません")
            return 0
        
        downloaded_count = 0
        skipped_count = 0
        page = 1
        max_pages = 10  # 最大10ページまで検索
        
        while downloaded_count < target_count and page <= max_pages:
            # より多くの候補を取得するため、ページあたりの取得数を増やす
            photos, total_pages = self.search_wallpapers(
                query, 
                30,  # 1ページあたり最大30件取得
                resolution, 
                orientation,
                page
            )
            
            if not photos:
                print(f"❌ ページ{page}で画像が見つかりませんでした")
                break
            
            page_downloaded = 0
            page_skipped = 0
            
            for photo in photos:
                if downloaded_count >= target_count:
                    break
                
                result = self.download_image(photo, resolution, theme_name, query)
                if result == "SKIPPED":
                    page_skipped += 1
                    skipped_count += 1
                elif result:  # 成功した場合
                    page_downloaded += 1
                    downloaded_count += 1
                
                # API制限を考慮して少し待機
                time.sleep(0.5)
            
            print(f"📄 ページ{page}: 新規{page_downloaded}枚、スキップ{page_skipped}枚 (累計: 新規{downloaded_count}/{target_count}枚)")
            
            # これ以上ページがない場合は終了
            if page >= total_pages:
                print(f"ℹ️  全ページ検索完了 (総ページ数: {total_pages})")
                break
                
            page += 1
        
        if downloaded_count < target_count:
            shortage = target_count - downloaded_count
            print(f"⚠️  目標枚数に{shortage}枚不足しています (テーマ: {theme_name})")
        
        print(f"📁 {theme_name}: 新規{downloaded_count}枚、既存スキップ{skipped_count}枚")
        return downloaded_count
    
    def collect_wallpapers_from_config(self, config_file="ToolSettings.json"):
        """
        設定ファイルから壁紙を収集
        
        Args:
            config_file (str): 設定ファイル名
        """
        config = self.load_themes_config(config_file)
        if not config:
            return
        
        settings = config.get("settings", {})
        themes = config.get("themes", [])
        
        # 有効なテーマのみを抽出
        enabled_themes = [theme for theme in themes if theme.get("enabled", True)]
        
        if not enabled_themes:
            print("❌ 有効なテーマが設定されていません")
            return
        
        total_downloaded = 0
        count_per_theme = settings.get("count_per_theme", 5)
        
        print(f"🚀 GetFreeWallpapers - 壁紙収集を開始します")
        print(f"📝 有効なテーマ数: {len(enabled_themes)}")
        print(f"📊 各テーマ {count_per_theme}枚ずつ取得（フルHD以上の横長画像のみ）")
        print(f"💾 保存先: {self.download_dir}")
        print(f"🗄️  データベース: {self.db_path}")
        print("-" * 50)
        
        for i, theme_config in enumerate(enabled_themes, 1):
            print(f"\n[{i}/{len(enabled_themes)}] テーマ処理中...")
            theme_downloaded = self.collect_theme_wallpapers(theme_config, settings)
            total_downloaded += theme_downloaded
            print("-" * 30)
        
        print(f"\n🎉 収集完了！合計 {total_downloaded}枚のフルHD以上壁紙を新規ダウンロードしました")
        print(f"📂 画像保存場所: {self.download_dir}")
        print(f"🗄️  データベース: {self.db_path}")
        
        # データベース統計を表示
        self.show_database_stats()
    
    def show_database_stats(self):
        """
        データベースの統計情報を表示
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 総画像数
            cursor.execute('SELECT COUNT(*) FROM wallpapers')
            total_count = cursor.fetchone()[0]
            
            # テーマ別統計
            cursor.execute('''
                SELECT theme_name, COUNT(*) as count 
                FROM wallpapers 
                WHERE theme_name IS NOT NULL 
                GROUP BY theme_name 
                ORDER BY count DESC
            ''')
            theme_stats = cursor.fetchall()
            
            # 撮影者別統計（上位5名）
            cursor.execute('''
                SELECT photographer, COUNT(*) as count 
                FROM wallpapers 
                GROUP BY photographer 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            photographer_stats = cursor.fetchall()
            
            # 総ファイルサイズ
            cursor.execute('SELECT SUM(file_size) FROM wallpapers WHERE file_size IS NOT NULL')
            total_size_result = cursor.fetchone()[0]
            total_size_mb = round(total_size_result / (1024 * 1024), 2) if total_size_result else 0
            
            conn.close()
            
            print("\n" + "="*50)
            print("📊 データベース統計")
            print("="*50)
            print(f"🖼️  総画像数: {total_count}枚")
            print(f"💾 総ファイルサイズ: {total_size_mb} MB")
            
            if theme_stats:
                print(f"\n🎨 テーマ別統計:")
                for theme, count in theme_stats:
                    print(f"   • {theme}: {count}枚")
            
            if photographer_stats:
                print(f"\n📸 撮影者別統計 (上位5名):")
                for photographer, count in photographer_stats:
                    print(f"   • {photographer}: {count}枚")
            
        except Exception as e:
            print(f"❌ 統計表示エラー: {e}")
    
    def export_metadata_to_json(self, output_file="wallpaper_metadata.json"):
        """
        データベースからメタデータをJSONファイルにエクスポート
        
        Args:
            output_file (str): 出力JSONファイル名
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, description, photographer, photographer_url, unsplash_url,
                       download_date, license, tags, width, height, image_file,
                       theme_name, theme_query, file_size, resolution
                FROM wallpapers
                ORDER BY download_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # データを辞書のリストに変換
            columns = ['id', 'description', 'photographer', 'photographer_url', 'unsplash_url',
                      'download_date', 'license', 'tags', 'width', 'height', 'image_file',
                      'theme_name', 'theme_query', 'file_size', 'resolution']
            
            export_data = []
            for row in results:
                data = dict(zip(columns, row))
                # tagsをJSONから元に戻す
                if data['tags']:
                    try:
                        data['tags'] = json.loads(data['tags'])
                    except:
                        data['tags'] = []
                export_data.append(data)
            
            # JSONファイルに出力
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ メタデータを {output_file} にエクスポートしました ({len(export_data)}件)")
            
        except Exception as e:
            print(f"❌ エクスポートエラー: {e}")

def main():
    # ここにあなたのUnsplash APIキーを設定してください
    API_KEY = "PIjfN_jat7xYlFUpFKMmvv_a9HU-YTwT9CkhKeZgGt4"  # https://unsplash.com/developers で取得
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("❌ エラー: APIキーを設定してください")
        print("1. https://unsplash.com/developers にアクセス")
        print("2. アプリケーションを作成")
        print("3. Access Keyを取得")
        print("4. スクリプト内のAPI_KEYを置き換えてください")
        return
    
    # 壁紙収集ツールを初期化
    collector = GetFreeWallpapers(API_KEY)
    
    # 設定ファイルから壁紙を収集
    collector.collect_wallpapers_from_config("ToolSettings.json")
    
    # オプション: メタデータをJSONにエクスポート
    # collector.export_metadata_to_json()

if __name__ == "__main__":
    main()