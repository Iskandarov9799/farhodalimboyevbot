import sqlite3
import os

DB_PATH = "database/bot.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database topilmadi. bot.py ni ishga tushiring.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Mavjud ustunlarni tekshirish
    cursor.execute("PRAGMA table_info(questions)")
    columns = [row[1] for row in cursor.fetchall()]
    print("Mavjud ustunlar:", columns)

    # image_file_id ustunini qo'shish
    if 'image_file_id' not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN image_file_id TEXT")
        print("✅ image_file_id ustuni qo'shildi!")
    else:
        print("ℹ️  image_file_id allaqachon mavjud.")

    # test_results da difficulty ustunini tekshirish
    cursor.execute("PRAGMA table_info(test_results)")
    result_cols = [row[1] for row in cursor.fetchall()]
    if 'difficulty' not in result_cols:
        cursor.execute("ALTER TABLE test_results ADD COLUMN difficulty TEXT DEFAULT 'mixed'")
        print("✅ test_results.difficulty ustuni qo'shildi!")
    else:
        print("ℹ️  difficulty allaqachon mavjud.")

    conn.commit()
    conn.close()
    print("\n✅ Migration tugadi!")

if __name__ == "__main__":
    migrate()
