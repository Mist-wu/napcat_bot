import aiosqlite
import asyncio
import datetime

DB_PATH = 'data/context_memory.db'

class ContextMemory:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS context (
                owner_type TEXT,     -- 'private' 或 'group'
                owner_id TEXT,       -- QQ号或群号
                user_id TEXT,        -- 发言用户QQ号
                message TEXT,
                timestamp TEXT
            )
            """)
            await db.commit()

    async def add_message(self, owner_type, owner_id, user_id, message):
        ts = datetime.datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO context (owner_type, owner_id, user_id, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (owner_type, str(owner_id), str(user_id), message, ts)
            )
            await db.commit()

    async def get_context(self, owner_type, owner_id, user_id=None, limit=30, mode="mix", user_limit=10, group_limit=20):
        async with aiosqlite.connect(self.db_path) as db:
            # 私聊，保持原样
            if owner_type == 'private' or not user_id or mode == "group_only":
                cur = await db.execute(
                    "SELECT message FROM context WHERE owner_type=? AND owner_id=? ORDER BY timestamp DESC LIMIT ?",
                    (owner_type, str(owner_id), limit)
                )
                rows = await cur.fetchall()
                return [row[0] for row in reversed(rows)]

            if mode == "user_only":
                cur = await db.execute(
                    "SELECT message FROM context WHERE owner_type='group' AND owner_id=? AND user_id=? ORDER BY timestamp DESC LIMIT ?",
                    (str(owner_id), str(user_id), limit)
                )
                rows = await cur.fetchall()
                return [row[0] for row in reversed(rows)]

            # mix模式：该用户N条+其他人M条，按时间排序，避免重复
            if mode == "mix":
                cur1 = await db.execute(
                    "SELECT rowid, message, timestamp FROM context WHERE owner_type='group' AND owner_id=? AND user_id=? ORDER BY timestamp DESC LIMIT ?",
                    (str(owner_id), str(user_id), user_limit)
                )
                rows1 = await cur1.fetchall()

                cur2 = await db.execute(
                    "SELECT rowid, message, timestamp FROM context WHERE owner_type='group' AND owner_id=? AND user_id!=? ORDER BY timestamp DESC LIMIT ?",
                    (str(owner_id), str(user_id), group_limit)
                )
                rows2 = await cur2.fetchall()

                # 合并、去重、升序
                all_rows = {row[0]: row for row in list(rows1) + list(rows2)}
                merged = list(all_rows.values())
                merged.sort(key=lambda x: x[2])  # 升序
                return [row[1] for row in merged]

            # fallback
            cur = await db.execute(
                "SELECT message FROM context WHERE owner_type='group' AND owner_id=? ORDER BY timestamp DESC LIMIT ?",
                (str(owner_id), limit)
            )
            rows = await cur.fetchall()
            return [row[0] for row in reversed(rows)]

    async def count_context(self, owner_type, owner_id, user_id=None):
        async with aiosqlite.connect(self.db_path) as db:
            if owner_type == 'private':
                cur = await db.execute(
                    "SELECT COUNT(*) FROM context WHERE owner_type='private' AND owner_id=?",
                    (str(owner_id),)
                )
            else:
                cur = await db.execute(
                    "SELECT COUNT(*) FROM context WHERE owner_type='group' AND owner_id=?",
                    (str(owner_id),)
                )
            row = await cur.fetchone()
        return row[0]

    async def summarize_and_shrink(self, owner_type, owner_id, ai_client, user_id=None):
        # 获取最早的15条，调用AI总结后，删掉原内容只保留总结
        async with aiosqlite.connect(self.db_path) as db:
            if owner_type == 'private':
                cur = await db.execute(
                    "SELECT rowid, message FROM context WHERE owner_type='private' AND owner_id=? ORDER BY timestamp ASC LIMIT 15",
                    (str(owner_id),)
                )
            else:
                cur = await db.execute(
                    "SELECT rowid, message FROM context WHERE owner_type='group' AND owner_id=? ORDER BY timestamp ASC LIMIT 15",
                    (str(owner_id),)
                )
            rows = await cur.fetchall()
        if not rows:
            return
        summary_prompt = "请把下面的对话内容做全面要点总结，不丢失关键信息作为长期上下文历史（不要输出不相关内容）：\n" + "\n".join(row[1] for row in rows)
        summary = await ai_client.call(summary_prompt)
        # 删除早期15条，插入精简化总结
        del_ids = tuple(row[0] for row in rows)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"DELETE FROM context WHERE rowid IN ({','.join('?'*len(del_ids))})", del_ids
            )
            await db.execute(
                "INSERT INTO context (owner_type, owner_id, user_id, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (owner_type, str(owner_id), user_id or '', f"[历史总结]{summary}", datetime.datetime.now().isoformat())
            )
            await db.commit()