import mysql.connector
from mysql.connector import Error

try:
    # 建立连接
    connection = mysql.connector.connect(
        host='localhost',      # 数据库地址
        user='root',  # 用户名
        password='rootpassword',  # 密码
        database='test_db',   # 数据库名
        port=32768
    )
    
    if connection.is_connected():
        print("成功连接到MySQL数据库")
        
        # 创建游标对象
        cursor = connection.cursor()
        
        # 执行SQL查询
        cursor.execute("SELECT VERSION()")
        
        # 获取结果
        result = cursor.fetchone()
        print("MySQL数据库版本:", result[0])
        
except Error as e:
    print(f"连接错误: {e}")
    
finally:
    # 关闭连接
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL连接已关闭")
