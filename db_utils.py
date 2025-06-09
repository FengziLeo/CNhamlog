
import mysql.connector
from mysql.connector import pooling
import threading
import traceback
import configparser
import os

# 读取配置文件(显式指定UTF-8编码)
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
with open(config_path, 'r', encoding='utf-8') as f:
    config.read_file(f)

# 从配置文件获取数据库配置
db_config = {
    "host": config.get('DB_CONFIG', 'host'),
    "port": config.getint('DB_CONFIG', 'port'),
    "user": config.get('DB_CONFIG', 'user'),
    "password": config.get('DB_CONFIG', 'password'),
    "database": config.get('DB_CONFIG', 'database'),
    "charset": config.get('DB_CONFIG', 'charset', fallback='utf8mb4'),
    "pool_size": config.getint('DB_CONFIG', 'pool_size', fallback=5),
    "pool_name": config.get('DB_CONFIG', 'pool_name', fallback='qso_pool'),
    "pool_reset_session": config.getboolean('DB_CONFIG', 'pool_reset_session', fallback=True)
}

# 全局连接池
db_pool = None
db_local = threading.local()

def init_db_pool():
    global db_pool
    print("正在使用的数据库配置：")
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"User: {db_config['user']}")
    print(f"Database: {db_config['database']}")

    try:
        db_pool = pooling.MySQLConnectionPool(**db_config)
        print("MySQL连接池初始化成功")
        return True
    except mysql.connector.Error as err:
        print(f"MySQL连接错误 [{err.errno}]: {err.msg}")
        print(traceback.format_exc())
        raise SystemExit("数据库连接失败，请检查配置和网络连接")
    except Exception as e:
        print(f"未知错误: {str(e)}")
        print(traceback.format_exc())
        raise SystemExit("无法初始化数据库连接池")

def get_db_connection():
    if db_pool is None:
        raise RuntimeError("数据库连接池未初始化")
    if not hasattr(db_local, 'conn'):
        db_local.conn = db_pool.get_connection()
    return db_local.conn

def close_db_connection(exception=None):
    if hasattr(db_local, 'conn'):
        db_local.conn.close()
        del db_local.conn

def execute_query(query, params=None, fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
        return result
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        close_db_connection()

def check_column_exists(table_name, column_name):
    """检查表中是否已存在指定列"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"""
            SELECT COUNT(*) AS count 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND COLUMN_NAME = '{column_name}'
        """)
        return cursor.fetchone()['count'] > 0
    finally:
        cursor.close()
        close_db_connection()

def alter_table_add_columns():
    """安全地添加表列(仅添加不存在的列)"""
    columns_to_add = [
        ('dxcc', 'VARCHAR(10)'),
        ('grid', 'VARCHAR(10)'),
        ('province', 'VARCHAR(20)'),
        ('band', 'VARCHAR(10)'),
        ('qslcard', 'TINYINT DEFAULT 0 COMMENT \'0-未发卡,1-已发卡,2-eyeball\''),
        ('confirmed', 'BOOLEAN DEFAULT FALSE'),
        ('sync_status', 'TINYINT DEFAULT 0 COMMENT \'0-未同步,1-同步中,2-已同步,3-同步失败\''),
        ('last_sync_time', 'DATETIME'),
        ('lotw_qsl_rcvd', 'VARCHAR(1) COMMENT \'Y-已收到,N-未收到\''),
        ('lotw_qsl_sent', 'VARCHAR(1) COMMENT \'Y-已发送,N-未发送\'')
    ]
    
    for column_name, column_def in columns_to_add:
        if not check_column_exists('qso_log', column_name):
            execute_query(f"ALTER TABLE qso_log ADD COLUMN {column_name} {column_def}")
            print(f"已成功添加列: {column_name}")