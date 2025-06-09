
"""
LOTW (Logbook of the World) 交互处理模块
功能：提交日志到LOTW和从LOTW下载日志
"""

import requests
from datetime import datetime
import xml.etree.ElementTree as ET
import logging
from configparser import ConfigParser
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LOTWHandler:
    """处理与LOTW网站交互的类"""
    
    def __init__(self, config_file='config.ini'):
        """
        初始化LOTW处理器
        :param config_file: 配置文件路径
        """
        self.config = ConfigParser()
        # 使用 with 语句打开文件，并指定 encoding 为 utf-8
        with open(config_file, 'r', encoding='utf-8') as fp:
            self.config.read_file(fp)
        
        self.base_url = "https://lotw.arrl.org/lotwuser/lotwreport.adi"
        self.session = requests.Session()
        
        # 从配置加载认证信息
        self.username = self.config.get('LOTW', 'username', fallback=None)
        self.password = self.config.get('LOTW', 'password', fallback=None)
        
        if not self.username or not self.password:
            logger.error("LOTW认证信息未配置")
            raise ValueError("请在config.ini中配置LOTW用户名和密码")

    def submit_log(self, log_data, qso_date=None):
        """
        提交日志到LOTW
        :param log_data: ADI格式的日志数据
        :param qso_date: 指定日期范围的QSO (可选)
        :return: 提交结果
        """
        params = {
            'login': self.username,
            'password': self.password,
            'cmd': 'upload'
        }
        
        if qso_date:
            params['qso_date'] = qso_date.strftime('%Y-%m-%d')
        
        try:
            response = self.session.post(
                self.base_url,
                params=params,
                files={'upfile': ('log.adi', log_data)}
            )
            response.raise_for_status()
            
            # 解析LOTW返回的XML响应
            root = ET.fromstring(response.text)
            if root.find('status').text == 'OK':
                logger.info("日志成功提交到LOTW")
                return True
            else:
                error_msg = root.find('error').text if root.find('error') is not None else "未知错误"
                logger.error(f"LOTW提交失败: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"提交日志到LOTW时出错: {str(e)}")
            return False

    def download_log(self, start_date=None, end_date=None):
        """
        从LOTW下载QSL日志并自动保存到项目download目录
        :param start_date: 开始日期(可选)，datetime对象
        :param end_date: 结束日期(可选)，datetime对象
        :return: (success, message)元组，success为布尔值表示是否成功，
                 message为结果描述或错误信息
        """
        params = {
            'login': self.username,
            'password': self.password,
            'qso_query': '1',
            'qso_withown': 'yes',
            'qso_qslsince': '1900-01-01'
        }
        
        try:
            # 处理日期参数
            if start_date:
                if not isinstance(start_date, datetime):
                    raise ValueError("start_date必须是datetime对象")
                params['qso_startdate'] = start_date.strftime('%Y-%m-%d')
                
            if end_date:
                if not isinstance(end_date, datetime):
                    raise ValueError("end_date必须是datetime对象")
                params['qso_enddate'] = end_date.strftime('%Y-%m-%d')

            # 准备下载目录
            download_dir = os.path.join(os.path.dirname(__file__), 'download')
            os.makedirs(download_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lotw_log_qsl_{timestamp}.adi"
            filepath = os.path.join(download_dir, filename)
            
            # 发送请求
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
    # 验证响应内容
            if 'application/x-arrl-adif' not in response.headers.get('Content-Type', ''):
                error_msg = "LOTW返回了无效的ADIF格式数据，可能是认证失败或服务不可用"
                logger.error(error_msg)
                return (False, error_msg)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
                success_msg = f"日志已成功下载并保存到：{filepath}"
            logger.info(success_msg)
            return (True, success_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败：{str(e)}。请检查网络连接和LOTW服务状态"
            logger.error(error_msg)
            return (False, error_msg)
            
        except IOError as e:
            error_msg = f"文件保存失败：{str(e)}。请检查目录权限和磁盘空间"
            logger.error(error_msg)
            return (False, error_msg)
            
        except ValueError as e:
            error_msg = f"参数错误：{str(e)}"
            logger.error(error_msg)
            return (False, error_msg)
            
        except Exception as e:
            error_msg = f"处理LOTW日志时发生意外错误：{str(e)}"
            logger.error(error_msg)
            return (False, error_msg)

    def download_log_QSO(self, start_date=None, end_date=None, auto_process=True):
        """
        从LOTW下载全部QSO记录并可选自动处理
        :param start_date: 开始日期(可选)，datetime对象，未指定则默认为1900-01-01
        :param end_date: 结束日期(可选)，datetime对象，未指定则默认为当前日期
        :param auto_process: 是否自动处理下载的文件(默认True)
        :return: 如果auto_process为False，返回(success, message)元组；
                 如果auto_process为True，返回(success, message, added, updated)元组
        """


        # 从配置中获取呼号和密码
        callsign = self.config.get('LOTW', 'username', fallback=None)
        password = self.config.get('LOTW', 'password', fallback=None)
        
        if not callsign or not password:
            error_msg = "LOTW认证信息未配置，请检查config.ini"
            logger.error(error_msg)
            return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)

        # 构建请求URL
        base_url = f"https://lotw.arrl.org/lotwuser/lotwreport.adi?login={callsign}&password={password}&qso_query=1&qso_qsl=no"
        
        try:
            # 处理日期参数
            if not start_date:
                start_date = datetime(1900, 1, 1)
            if not end_date:
                end_date = datetime.now()
                
            if not isinstance(start_date, datetime):
                raise ValueError("start_date必须是datetime对象")
            if not isinstance(end_date, datetime):
                raise ValueError("end_date必须是datetime对象")
                
            base_url += f"&qso_startdate={start_date.strftime('%Y-%m-%d')}"
            base_url += f"&qso_enddate={end_date.strftime('%Y-%m-%d')}"

            # 准备下载目录
            download_dir = os.path.join(os.path.dirname(__file__), 'download')
            os.makedirs(download_dir, exist_ok=True)
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"lotw_qso_{timestamp}.adi"
            filepath = os.path.join(download_dir, filename)
            
            # 发送请求
            response = self.session.get(base_url, timeout=30)
            response.raise_for_status()
            
            # 验证响应内容
            if 'application/x-arrl-adif' not in response.headers.get('Content-Type', ''):
                error_msg = "LOTW返回了无效的ADIF格式数据，可能是认证失败或服务不可用"
                logger.error(error_msg)
                return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)
            
            # 保存文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            success_msg = f"全部QSO记录已成功下载并保存到：{filepath}"
            logger.info(success_msg)
            
            if auto_process:
                added, updated = self.process_adi_file(filepath)
                return (True, success_msg, added, updated)
            else:
                return (True, success_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败：{str(e)}。请检查网络连接和LOTW服务状态"
            logger.error(error_msg)
            return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)
            
        except IOError as e:
            error_msg = f"文件保存失败：{str(e)}。请检查目录权限和磁盘空间"
            logger.error(error_msg)
            return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)
            
        except ValueError as e:
            error_msg = f"参数错误：{str(e)}"
            logger.error(error_msg)
            return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)
            
        except Exception as e:
            error_msg = f"处理LOTW QSO记录时发生意外错误：{str(e)}"
            logger.error(error_msg)
            return (False, error_msg) if not auto_process else (False, error_msg, 0, 0)



    def process_adi_file(self, filepath):
        """
        处理从LOTW下载的ADI文件，与本地数据库比较并更新
        :param filepath: ADI文件路径
        :return: (新增记录数, 更新记录数)元组
        """
        from db_utils import execute_query
        import re
        
        # 解析ADI文件
        with open(filepath, 'r', encoding='utf-8') as f:
            adi_content = f.read()
        
        # ADI记录解析正则表达式
        record_pattern = re.compile(
            r'<([^>:]+):(\d+)>([^<]*)',
            re.IGNORECASE | re.DOTALL
        )
        
        # 分割记录
        records = []
        current_record = {}
        for tag, length, value in record_pattern.findall(adi_content):
            tag = tag.upper()
            value = value.strip()[:int(length)]
            
            if tag == 'EOR':
                if current_record:
                    records.append(current_record)
                    current_record = {}
            else:
                current_record[tag] = value
        
        added = 0
        updated = 0
        
        for record in records:
            # 检查必要字段
            if not all(k in record for k in ['CALL', 'QSO_DATE', 'TIME_ON', 'BAND', 'MODE']):
                continue
            
            # 构建查询条件
            conditions = {
                'callsign': record['CALL'],
                'qso_date': record['QSO_DATE'],
                'time_on': record['TIME_ON'],
                'band': record['BAND'],
                'mode': record['MODE']
            }
            
            # 检查记录是否存在
            existing = execute_query("""
                SELECT id, confirmed FROM qso_log 
                WHERE callsign = %(callsign)s 
                AND qso_date = %(qso_date)s 
                AND time_on = %(time_on)s 
                AND band = %(band)s 
                AND mode = %(mode)s
                LIMIT 1
            """, conditions, fetch=True)
            
            # 处理LOTW确认状态
            lotw_confirmed = record.get('LOTW_QSL_RCVD', '').upper() == 'Y'
            
            if not existing:
                # 插入新记录
                new_record = conditions.copy()
                new_record.update({
                    'confirmed': 1 if lotw_confirmed else 0,
                    'lotw_qsl_rcvd': 'Y' if lotw_confirmed else 'N',
                    'dxcc': record.get('DXCC'),
                    'grid': record.get('GRIDSQUARE'),
                    'province': record.get('STATE')
                })
                
                execute_query("""
                    INSERT INTO qso_log (
                        callsign, qso_date, time_on, band, mode,
                        dxcc, grid, province, confirmed, lotw_qsl_rcvd
                    ) VALUES (
                        %(callsign)s, %(qso_date)s, %(time_on)s, %(band)s, %(mode)s,
                        %(dxcc)s, %(grid)s, %(province)s, %(confirmed)s, %(lotw_qsl_rcvd)s
                    )
                """, new_record)
                added += 1
            elif not existing[0]['confirmed'] and lotw_confirmed:
                # 更新确认状态
                execute_query("""
                    UPDATE qso_log 
                    SET confirmed = 1, 
                        lotw_qsl_rcvd = 'Y',
                        last_sync_time = NOW() 
                    WHERE id = %s
                """, (existing[0]['id'],))
                updated += 1
        
        return (added, updated)

    def convert_to_adi(self, qso_records):
        """
        将QSO记录转换为ADI格式
        :param qso_records: QSO记录列表
        :return: ADI格式字符串
        """
        adi_header = """Generated by QSL Logger
                    <ADIF_VER:5>3.1.0
                    <PROGRAMID:11>QSL Logger
                    <PROGRAMVERSION:5>1.0.0
                    <EOH>
                    """
        adi_lines = []
        
        for qso in qso_records:
            adi_line = []
            for field, value in qso.items():
                if value:
                    adi_line.append(f"<{field.upper()}:{len(str(value))}>{value}")
            adi_lines.append("".join(adi_line) + "<EOR>")
        
        return adi_header + "\n".join(adi_lines)


if __name__ == "__main__":
    # 示例用法
    handler = LOTWHandler()
    
    # 示例：下载最近30天的日志
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    log_data = handler.download_log_QSO()
    
    if log_data:
        print(f"下载到{len(log_data)}字符的日志数据")
