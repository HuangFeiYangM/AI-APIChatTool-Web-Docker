import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        port=32768,
        user='root',
        password='rootpassword',
        database='test_db'
    )
    print("数据库连接成功！")
    connection.close()
except Exception as e:
    print(f"数据库连接失败: {e}")