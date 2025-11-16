import mysql.connector

try:
    conn = mysql.connector.connect(
        host='localhost',
        port=32769,
        user='root',
        password='rootpassword',
        database='test_db'
    )
    print("mysql-connector-python 连接成功!")
    
    # 执行简单查询
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"MySQL 版本: {version[0]}")
    
    conn.close()
except Exception as e:
    print(f"连接失败: {e}")
