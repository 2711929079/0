import sqlite3

# 连接数据库
conn = sqlite3.connect('data/memory_database.db')
cursor = conn.cursor()

# 检查数据库表结构
print("=== 数据库表结构 ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", [table[0] for table in tables])

# 检查chat_messages表结构
print("\n=== chat_messages表结构 ===")
cursor.execute("PRAGMA table_info(chat_messages);")
columns = cursor.fetchall()
for col in columns:
    print(f"列: {col[1]}, 类型: {col[2]}, 是否为空: {col[3]}, 默认值: {col[4]}")

# 检查聊天记录数据
print("\n=== 聊天记录数据 ===")
cursor.execute("SELECT COUNT(*) FROM chat_messages;")
count = cursor.fetchone()[0]
print(f"聊天记录总数: {count}")

# 查看最新的10条聊天记录
cursor.execute("""
    SELECT id, user_id, role, message_type, content, audio_url, timestamp 
    FROM chat_messages 
    ORDER BY timestamp DESC 
    LIMIT 10;
""")
messages = cursor.fetchall()

print("\n最新的10条聊天记录:")
for i, msg in enumerate(messages, 1):
    print(f"\n{i}. ID: {msg[0]}")
    print(f"   用户ID: {msg[1]}")
    print(f"   角色: {msg[2]}")
    print(f"   消息类型: {msg[3]}")
    print(f"   内容: {msg[4][:100]}..." if len(msg[4]) > 100 else f"   内容: {msg[4]}")
    print(f"   音频URL: {msg[5]}")
    print(f"   时间戳: {msg[6]}")

# 检查users表
print("\n=== users表数据 ===")
cursor.execute("SELECT * FROM users;")
users = cursor.fetchall()
print(f"用户总数: {len(users)}")
for user in users:
    print(f"用户ID: {user[0]}, 创建时间: {user[1]}, 最后登录: {user[2]}")

# 关闭连接
conn.close()

print("\n=== 数据库检查完成 ===")