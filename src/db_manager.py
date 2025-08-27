#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Manager - 壁紙データベース管理ユーティリティ

機能:
- データベース内容の表示・検索
- メタデータのエクスポート/インポート
- データベースのメンテナンス
- 統計情報の表示
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime

class WallpaperDBManager:
    def __init__(self):
        """データベース管理ツールの初期化"""
        # srcフォルダと同じ階層のデータベースファイル
        current_dir = Path(__file__).parent
        if current_dir.name == "src":
            project_root = current_dir.parent
        else:
            project_root = current_dir
        
        self.db_path = project_root / "db/wallpapers.db"
        
        if not self.db_path.exists():
            print(f"❌ データベースファイルが見つかりません: {self.db_path}")
            sys.exit(1)
    
    def show_all_wallpapers(self, limit=50):
        """
        全ての壁紙を表示
        
        Args:
            limit (int): 表示件数制限
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, photographer, description, theme_name, 
                       width, height, file_size, download_date
                FROM wallpapers 
                ORDER BY download_date DESC 
                LIMIT ?
            ''', (limit,))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                print("📭 データベースに壁紙が登録されていません")
                return
            
            print(f"🖼️  登録されている壁紙 (最新{len(results)}件)")
            print("="*80)
            print(f"{'ID':<15} {'撮影者':<20} {'テーマ':<15} {'サイズ':<12} {'ダウンロード日':<12}")
            print("-"*80)
            
            for row in results:
                photo_id, photographer, description, theme_name, width, height, file_size, download_date = row
                size_str = f"{width}x{height}" if width and height else "不明"
                date_str = download_date[:10] if download_date else "不明"
                theme_str = theme_name[:14] if theme_name else "不明"
                photographer_str = photographer[:19] if photographer else "不明"
                
                print(f"{photo_id:<15} {photographer_str:<20} {theme_str:<15} {size_str:<12} {date_str:<12}")
                
        except Exception as e:
            print(f"❌ データベース表示エラー: {e}")
    
    def search_by_theme(self, theme_name):
        """
        テーマで検索
        
        Args:
            theme_name (str): テーマ名
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, photographer, description, width, height, download_date
                FROM wallpapers 
                WHERE theme_name LIKE ?
                ORDER BY download_date DESC
            ''', (f"%{theme_name}%",))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                print(f"🔍 テーマ '{theme_name}' の壁紙が見つかりませんでした")
                return
            
            print(f"🎨 テーマ '{theme_name}' の壁紙 ({len(results)}件)")
            print("="*70)
            
            for row in results:
                photo_id, photographer, description, width, height, download_date = row
                size_str = f"{width}x{height}" if width and height else "不明"
                date_str = download_date[:10] if download_date else "不明"
                desc_str = description[:30] + "..." if description and len(description) > 30 else description or "説明なし"
                
                print(f"ID: {photo_id}")
                print(f"撮影者: {photographer}")
                print(f"説明: {desc_str}")
                print(f"サイズ: {size_str}")
                print(f"ダウンロード日: {date_str}")
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
    
    def search_by_photographer(self, photographer_name):
        """
        撮影者で検索
        
        Args:
            photographer_name (str): 撮影者名
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, description, theme_name, width, height, download_date
                FROM wallpapers 
                WHERE photographer LIKE ?
                ORDER BY download_date DESC
            ''', (f"%{photographer_name}%",))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                print(f"🔍 撮影者 '{photographer_name}' の壁紙が見つかりませんでした")
                return
            
            print(f"📸 撮影者 '{photographer_name}' の壁紙 ({len(results)}件)")
            print("="*70)
            
            for row in results:
                photo_id, description, theme_name, width, height, download_date = row
                size_str = f"{width}x{height}" if width and height else "不明"
                date_str = download_date[:10] if download_date else "不明"
                theme_str = theme_name or "不明"
                desc_str = description[:30] + "..." if description and len(description) > 30 else description or "説明なし"
                
                print(f"ID: {photo_id}")
                print(f"テーマ: {theme_str}")
                print(f"説明: {desc_str}")
                print(f"サイズ: {size_str}")
                print(f"ダウンロード日: {date_str}")
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
    
    def show_statistics(self):
        """
        データベース統計を詳細表示
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 基本統計
            cursor.execute('SELECT COUNT(*) FROM wallpapers')
            total_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(file_size) FROM wallpapers WHERE file_size IS NOT NULL')
            total_size_result = cursor.fetchone()[0]
            total_size_mb = round(total_size_result / (1024 * 1024), 2) if total_size_result else 0
            
            cursor.execute('SELECT MIN(download_date), MAX(download_date) FROM wallpapers')
            date_range = cursor.fetchone()
            
            # テーマ別統計
            cursor.execute('''
                SELECT theme_name, COUNT(*) as count 
                FROM wallpapers 
                WHERE theme_name IS NOT NULL 
                GROUP BY theme_name 
                ORDER BY count DESC
            ''')
            theme_stats = cursor.fetchall()
            
            # 撮影者別統計
            cursor.execute('''
                SELECT photographer, COUNT(*) as count 
                FROM wallpapers 
                GROUP BY photographer 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            photographer_stats = cursor.fetchall()
            
            # 解像度別統計
            cursor.execute('''
                SELECT resolution, COUNT(*) as count 
                FROM wallpapers 
                WHERE resolution IS NOT NULL
                GROUP BY resolution 
                ORDER BY count DESC
            ''')
            resolution_stats = cursor.fetchall()
            
            # 月別統計
            cursor.execute('''
                SELECT strftime('%Y-%m', download_date) as month, COUNT(*) as count
                FROM wallpapers 
                WHERE download_date IS NOT NULL
                GROUP BY month 
                ORDER BY month DESC
                LIMIT 12
            ''')
            monthly_stats = cursor.fetchall()
            
            conn.close()
            
            # 結果表示
            print("📊 壁紙データベース統計")
            print("="*60)
            print(f"🖼️  総画像数: {total_count:,}枚")
            print(f"💾 総ファイルサイズ: {total_size_mb:,} MB")
            
            if date_range[0] and date_range[1]:
                start_date = date_range[0][:10]
                end_date = date_range[1][:10]
                print(f"📅 収集期間: {start_date} ～ {end_date}")
            
            if theme_stats:
                print(f"\n🎨 テーマ別統計:")
                for theme, count in theme_stats:
                    percentage = (count / total_count) * 100 if total_count > 0 else 0
                    print(f"   • {theme}: {count}枚 ({percentage:.1f}%)")
            
            if photographer_stats:
                print(f"\n📸 撮影者別統計 (上位10名):")
                for photographer, count in photographer_stats:
                    percentage = (count / total_count) * 100 if total_count > 0 else 0
                    print(f"   • {photographer}: {count}枚 ({percentage:.1f}%)")
            
            if resolution_stats:
                print(f"\n🔍 解像度別統計:")
                for resolution, count in resolution_stats:
                    percentage = (count / total_count) * 100 if total_count > 0 else 0
                    print(f"   • {resolution}: {count}枚 ({percentage:.1f}%)")
            
            if monthly_stats:
                print(f"\n📈 月別統計 (最新12ヶ月):")
                for month, count in monthly_stats:
                    print(f"   • {month}: {count}枚")
                
        except Exception as e:
            print(f"❌ 統計表示エラー: {e}")
    
    def export_to_json(self, output_file="wallpaper_export.json"):
        """
        データベース全体をJSONファイルにエクスポート
        
        Args:
            output_file (str): 出力ファイル名
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, description, photographer, photographer_url, unsplash_url,
                       download_date, license, tags, width, height, image_file,
                       theme_name, theme_query, file_size, resolution, created_at
                FROM wallpapers
                ORDER BY download_date DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # データを辞書のリストに変換
            columns = ['id', 'description', 'photographer', 'photographer_url', 'unsplash_url',
                      'download_date', 'license', 'tags', 'width', 'height', 'image_file',
                      'theme_name', 'theme_query', 'file_size', 'resolution', 'created_at']
            
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
            
            # エクスポート情報を追加
            export_info = {
                'export_date': datetime.now().isoformat(),
                'total_records': len(export_data),
                'database_path': str(self.db_path),
                'records': export_data
            }
            
            # JSONファイルに出力
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_info, f, ensure_ascii=False, indent=2)
            
            print(f"✅ データベースを {output_file} にエクスポートしました")
            print(f"📊 エクスポート件数: {len(export_data)}件")
            
        except Exception as e:
            print(f"❌ エクスポートエラー: {e}")
    
    def cleanup_missing_files(self):
        """
        実際のファイルが存在しないレコードをデータベースから削除
        """
        try:
            downloads_folder = Path.home() / "Downloads" / "gfp"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, image_file FROM wallpapers')
            all_records = cursor.fetchall()
            
            deleted_count = 0
            for photo_id, image_file in all_records:
                file_path = downloads_folder / image_file
                if not file_path.exists():
                    cursor.execute('DELETE FROM wallpapers WHERE id = ?', (photo_id,))
                    deleted_count += 1
                    print(f"🗑️  削除: {photo_id} - {image_file}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ クリーンアップ完了: {deleted_count}件のレコードを削除しました")
            
        except Exception as e:
            print(f"❌ クリーンアップエラー: {e}")
    
    def backup_database(self, backup_file=None):
        """
        データベースをバックアップ
        
        Args:
            backup_file (str): バックアップファイル名（省略時は自動生成）
        """
        try:
            if not backup_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"wallpapers_backup_{timestamp}.db"
            
            import shutil
            shutil.copy2(self.db_path, backup_file)
            
            print(f"✅ データベースをバックアップしました: {backup_file}")
            
        except Exception as e:
            print(f"❌ バックアップエラー: {e}")
    
    def delete_by_theme(self, theme_name):
        """
        指定テーマの壁紙を削除（ファイルも削除）
        
        Args:
            theme_name (str): 削除するテーマ名
        """
        try:
            downloads_folder = Path.home() / "Downloads" / "gfp"
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 削除対象の確認
            cursor.execute('''
                SELECT id, image_file FROM wallpapers 
                WHERE theme_name LIKE ?
            ''', (f"%{theme_name}%",))
            
            records_to_delete = cursor.fetchall()
            
            if not records_to_delete:
                print(f"🔍 テーマ '{theme_name}' の壁紙が見つかりませんでした")
                conn.close()
                return
            
            print(f"⚠️  テーマ '{theme_name}' の {len(records_to_delete)}枚を削除します")
            confirm = input("続行しますか？ (y/N): ")
            
            if confirm.lower() != 'y':
                print("❌ 削除をキャンセルしました")
                conn.close()
                return
            
            deleted_files = 0
            deleted_records = 0
            
            for photo_id, image_file in records_to_delete:
                # ファイル削除
                file_path = downloads_folder / image_file
                if file_path.exists():
                    file_path.unlink()
                    deleted_files += 1
                
                # データベースから削除
                cursor.execute('DELETE FROM wallpapers WHERE id = ?', (photo_id,))
                deleted_records += 1
                
                print(f"🗑️  削除: {image_file}")
            
            conn.commit()
            conn.close()
            
            print(f"✅ 削除完了: ファイル{deleted_files}件、レコード{deleted_records}件")
            
        except Exception as e:
            print(f"❌ 削除エラー: {e}")

def main():
    """メイン関数 - コマンドライン引数に基づいて機能を実行"""
    manager = WallpaperDBManager()
    
    if len(sys.argv) < 2:
        print("🔧 壁紙データベース管理ツール")
        print("="*40)
        print("使用方法:")
        print("  python db_manager.py [コマンド] [オプション]")
        print("\nコマンド:")
        print("  list [件数]          - 壁紙一覧表示（デフォルト50件）")
        print("  stats               - 統計情報表示")
        print("  search-theme [名前]  - テーマで検索")
        print("  search-photo [名前]  - 撮影者で検索")
        print("  export [ファイル名]   - JSONエクスポート")
        print("  cleanup             - 欠損ファイルのクリーンアップ")
        print("  backup [ファイル名]   - データベースバックアップ")
        print("  delete-theme [名前]  - テーマ削除（要確認）")
        print("\n例:")
        print("  python db_manager.py list 100")
        print("  python db_manager.py search-theme 自然")
        print("  python db_manager.py export my_wallpapers.json")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        manager.show_all_wallpapers(limit)
    
    elif command == "stats":
        manager.show_statistics()
    
    elif command == "search-theme":
        if len(sys.argv) < 3:
            print("❌ テーマ名を指定してください")
            return
        theme_name = sys.argv[2]
        manager.search_by_theme(theme_name)
    
    elif command == "search-photo":
        if len(sys.argv) < 3:
            print("❌ 撮影者名を指定してください")
            return
        photographer_name = sys.argv[2]
        manager.search_by_photographer(photographer_name)
    
    elif command == "export":
        output_file = sys.argv[2] if len(sys.argv) > 2 else "wallpaper_export.json"
        manager.export_to_json(output_file)
    
    elif command == "cleanup":
        manager.cleanup_missing_files()
    
    elif command == "backup":
        backup_file = sys.argv[2] if len(sys.argv) > 2 else None
        manager.backup_database(backup_file)
    
    elif command == "delete-theme":
        if len(sys.argv) < 3:
            print("❌ 削除するテーマ名を指定してください")
            return
        theme_name = sys.argv[2]
        manager.delete_by_theme(theme_name)
    
    else:
        print(f"❌ 未知のコマンド: {command}")
        print("使用可能なコマンド: list, stats, search-theme, search-photo, export, cleanup, backup, delete-theme")

if __name__ == "__main__":
    main()