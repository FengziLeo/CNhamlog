"""
This script runs the application using a development server.
"""

from flask import Flask
from db_utils import init_db_pool, execute_query
from routes import init_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# 初始化数据库连接池
init_db_pool()

# 更新数据库表结构
try:
    from db_utils import alter_table_add_columns
    alter_table_add_columns()
    print("数据库表结构更新成功")
except Exception as e:
    print(f"数据库表结构更新失败: {str(e)}")

# 初始化路由
init_routes(app)

if __name__ == '__main__':
    # 初始化数据库表
    init_query = """
    CREATE TABLE IF NOT EXISTS qso_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        callsign VARCHAR(10) NOT NULL,
        frequency FLOAT NOT NULL,
        mode VARCHAR(10) NOT NULL,
        equipment VARCHAR(50),
        antenna VARCHAR(50),
        power FLOAT,
        date DATE,
        time VARCHAR(10) NOT NULL,
        notes TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    execute_query(init_query)
    app.run(debug=True)
