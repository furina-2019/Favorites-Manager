import sqlite3
import os
import hashlib

class Database:
    def __init__(self, db_path="user_data.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 收藏夹表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 收藏项表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    folder_id INTEGER NOT NULL,
                    item_type TEXT NOT NULL,  -- 'link' or 'file'
                    title TEXT,
                    url TEXT,                 -- 对于链接存储URL，对于文件存储路径
                    category TEXT,            -- 用户自定义类别
                    cover_path TEXT,          -- 封面图片路径
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE CASCADE
                )
            ''')
            cursor.execute("PRAGMA table_info(folders)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'password_hash' not in columns:
                cursor.execute("ALTER TABLE folders ADD COLUMN password_hash TEXT")

            cursor.execute("PRAGMA table_info(items)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'password_hash' not in columns:
                cursor.execute("ALTER TABLE items ADD COLUMN password_hash TEXT")
            if 'summary' not in columns:
                cursor.execute("ALTER TABLE items ADD COLUMN summary TEXT")
            conn.commit()

    def add_folder(self, name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO folders (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

    def get_folders(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, password_hash, created_at FROM folders ORDER BY created_at DESC")
            return cursor.fetchall()
    
    def get_folder_item_count(self, folder_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM items WHERE folder_id = ?", (folder_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def add_item(self, folder_id, item_type, title, url_or_path, category, cover_path, summary=""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (folder_id, item_type, title, url, category, cover_path, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (folder_id, item_type, title, url_or_path, category, cover_path, summary))
            conn.commit()
            return cursor.lastrowid

    def get_items_by_folder(self, folder_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, item_type, title, url, category, cover_path, password_hash, summary, created_at FROM items WHERE folder_id = ?",
                (folder_id,))
            return cursor.fetchall()

    def rename_folder(self, folder_id, new_name):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE folders SET name = ? WHERE id = ?", (new_name, folder_id))
            conn.commit()

    def delete_folder(self, folder_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            conn.commit()

    def update_item(self, item_id, title, url_or_path, category, cover_path=None, summary=""):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE items 
                SET title = ?, url = ?, category = ?, cover_path = ?, summary = ?
                WHERE id = ?
            ''', (title, url_or_path, category, cover_path or "", summary, item_id))
            conn.commit()

    def update_item_category(self, item_id, category):
        """仅更新收藏项的类别"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET category = ? WHERE id = ?", (category, item_id))
            conn.commit()

    def delete_item(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()

    def delete_items_by_ids(self, item_ids):
        """批量删除收藏项"""
        if not item_ids:
            return
        placeholders = ','.join('?' * len(item_ids))
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM items WHERE id IN ({placeholders})", item_ids)
            conn.commit()

    import hashlib

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def set_folder_password(self, folder_id, password):
        hash_ = self._hash_password(password)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE folders SET password_hash = ? WHERE id = ?", (hash_, folder_id))
            conn.commit()

    def remove_folder_password(self, folder_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE folders SET password_hash = NULL WHERE id = ?", (folder_id,))
            conn.commit()

    def get_folder_password_hash(self, folder_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM folders WHERE id = ?", (folder_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def verify_folder_password(self, folder_id, password):
        hash_ = self.get_folder_password_hash(folder_id)
        if hash_ is None:
            return True
        return hash_ == self._hash_password(password)

    def set_item_password(self, item_id, password):
        hash_ = self._hash_password(password)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET password_hash = ? WHERE id = ?", (hash_, item_id))
            conn.commit()

    def remove_item_password(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE items SET password_hash = NULL WHERE id = ?", (item_id,))
            conn.commit()

    def get_item_password_hash(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM items WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return row[0] if row else None

    def verify_item_password(self, item_id, password):
        hash_ = self.get_item_password_hash(item_id)
        if hash_ is None:
            return True
        return hash_ == self._hash_password(password)

    def get_item_by_id(self, item_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT item_type, title, url, category, cover_path, password_hash, summary FROM items WHERE id = ?",
                           (item_id,))
            row = cursor.fetchone()
            return row if row else None

    def migrate_cover_paths(self):
        """迁移旧的封面路径从临时目录到持久化目录"""
        import tempfile
        import shutil
        
        temp_dir = tempfile.gettempdir()
        covers_dir = os.path.join(os.path.expanduser('~'), '.favourite', 'covers')
        os.makedirs(covers_dir, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, cover_path FROM items WHERE cover_path IS NOT NULL AND cover_path != ''")
            
            for item_id, cover_path in cursor.fetchall():
                # 检查是否是旧的临时路径
                if cover_path.startswith(temp_dir) and os.path.exists(cover_path):
                    # 生成新的持久化路径
                    filename = os.path.basename(cover_path)
                    new_path = os.path.join(covers_dir, filename)
                    
                    # 如果目标文件不存在，复制文件
                    if not os.path.exists(new_path):
                        try:
                            shutil.copy2(cover_path, new_path)
                            print(f"[MIGRATE] 迁移封面: {cover_path} -> {new_path}")
                        except Exception as e:
                            print(f"[ERROR] 迁移封面失败: {e}")
                            continue
                    
                    # 更新数据库中的路径
                    cursor.execute("UPDATE items SET cover_path = ? WHERE id = ?", (new_path, item_id))
            
            conn.commit()
