import asyncio
import aiosqlite
from pathlib import Path

async def inspect_memory():
    # Путь к базе данных
    db_path = Path("data/lre_core.db")
    
    if not db_path.exists():
        print(f"❌ Файл базы данных не найден: {db_path}")
        return

    print(f"📂 Читаем память из: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        
        # Запрашиваем последние 5 записей
        async with db.execute("SELECT timestamp, action, status, latency_ms, trace_id FROM decision_log ORDER BY timestamp DESC LIMIT 5") as cursor:
            rows = await cursor.fetchall()
            
            if not rows:
                print("📭 Память пуста! (Странно, если ты делал Ping)")
                return

            print("\n📊 ПОСЛЕДНИЕ ЗАПИСИ В МОЗГЕ:")
            print("=" * 100)
            print(f"{'TIME':<20} | {'ACTION':<15} | {'STATUS':<10} | {'LATENCY':<10} | {'TRACE ID'}")
            print("-" * 100)
            
            for row in rows:
                print(f"{row['timestamp']:<20.2f} | {row['action']:<15} | {row['status']:<10} | {row['latency_ms']:.2f}ms    | {row['trace_id']}")
            print("=" * 100)

if __name__ == "__main__":
    try:
        asyncio.run(inspect_memory())
    except Exception as e:
        print(f"Ошибка при чтении базы: {e}")