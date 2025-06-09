
from flask import render_template, request, jsonify
from forms import QSOForm
from db_utils import execute_query, get_db_connection
import json

def init_routes(app):
    # 页面路由
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/qso_form')
    def qso_form():
        form = QSOForm()
        return render_template('qso_form.html', form=form)

    @app.route('/log')
    def log():
        return render_template('log.html')

    @app.route('/log/new', methods=['POST'])
    def new_log():
        form = QSOForm()
        if form.validate_on_submit():
            try:
                query = """
                INSERT INTO qso_log (
                    callsign, frequency, mode, equipment, 
                    antenna, power, date, time, notes,
                    dxcc, grid, province, band, qslcard
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    form.callsign.data, form.frequency.data, form.mode.data,
                    form.equipment.data, form.antenna.data, form.power.data,
                    form.date.data, form.time.data, form.notes.data,
                    form.dxcc.data, form.grid.data, form.province.data,
                    form.band.data, int(form.qslcard.data)
                )
                execute_query(query, params)
                return jsonify({
                    "success": True,
                    "message": "日志添加成功",
                    "data": {
                        "callsign": form.callsign.data,
                        "frequency": form.frequency.data,
                        "mode": form.mode.data
                    }
                }), 201
            except Exception as e:
                return jsonify({
                    "success": False,
                    "message": str(e),
                    "error": "DATABASE_ERROR"
                }), 500
        return jsonify({
            "success": False,
            "message": "表单验证失败",
            "errors": form.errors,
            "error": "VALIDATION_ERROR"
        }), 400

    # API路由
    @app.route('/api/logs/count', methods=['GET'])
    def get_log_count():
        try:
            result = execute_query("SELECT COUNT(*) as count FROM qso_log", fetch=True)
            return jsonify({"success": True, "count": result[0]['count']})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/api/logs', methods=['GET'])
    def get_logs():
        try:
            all_records = request.args.get('all', 'false').lower() == 'true'
            
            if all_records:
                # 全量获取
                query = "SELECT * FROM qso_log ORDER BY date DESC, time DESC"
                logs = execute_query(query, fetch=True)
                return jsonify({
                    "success": True,
                    "data": logs,
                    "total": len(logs)
                })
            else:
                # 分页获取
                page = int(request.args.get('page', 1))
                size = int(request.args.get('size', 25))
                offset = (page - 1) * size

                query = """
                SELECT * FROM qso_log 
                ORDER BY date DESC, time DESC 
                LIMIT %s OFFSET %s
                """
                logs = execute_query(query, (size, offset), fetch=True)

                # 获取总数
                count_result = execute_query("SELECT COUNT(*) as total FROM qso_log", fetch=True)
                
                return jsonify({
                    "success": True,
                    "data": logs,
                    "total": count_result[0]['total'],
                    "pages": (count_result[0]['total'] + size - 1) // size,
                    "current_page": page
                })
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/api/logs/<int:log_id>', methods=['GET'])
    def get_log(log_id):
        try:
            query = "SELECT * FROM qso_log WHERE id = %s"
            log = execute_query(query, (log_id,), fetch=True)
            if not log:
                return jsonify({"success": False, "message": "日志不存在"}), 404
            return jsonify({"success": True, "data": log[0]})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/api/logs/<int:log_id>', methods=['PUT'])
    def update_log(log_id):
        try:
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "message": "请求数据不能为空"}), 400

            # 验证必填字段
            required_fields = ['callsign', 'frequency', 'mode']
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({
                        "success": False,
                        "message": f"字段 {field} 是必填项"
                    }), 400

            # 准备更新数据
            update_data = {
                'callsign': data.get('callsign', ''),
                'frequency': float(data.get('frequency', 0)),
                'mode': data.get('mode', ''),
                'equipment': data.get('equipment', ''),
                'antenna': data.get('antenna', ''),
                'power': float(data.get('power', 0)),
                'date': data.get('date', ''),
                'time': data.get('time', ''),
                'notes': data.get('notes', ''),
                'dxcc': data.get('dxcc', ''),
                'grid': data.get('grid', ''),
                'province': data.get('province', ''),
                'band': data.get('band', ''),
                'qslcard': int(data.get('qslcard', 0))
            }

            query = """
            UPDATE qso_log SET
                callsign = %(callsign)s,
                frequency = %(frequency)s,
                mode = %(mode)s,
                equipment = %(equipment)s,
                antenna = %(antenna)s,
                power = %(power)s,
                date = %(date)s,
                time = %(time)s,
                notes = %(notes)s,
                dxcc = %(dxcc)s,
                grid = %(grid)s,
                province = %(province)s,
                band = %(band)s,
                qslcard = %(qslcard)s
            WHERE id = %(id)s
            """
            params = {'id': log_id, **update_data}
            
            # 执行更新并记录
            app.logger.info(f"更新日志 {log_id}: {params}")
            execute_query(query, params)
            
            return jsonify({
                "success": True,
                "message": "日志更新成功",
                "data": {"id": log_id}
            })
        except ValueError as e:
            return jsonify({
                "success": False,
                "message": f"数据格式错误: {str(e)}"
            }), 400
        except Exception as e:
            app.logger.error(f"更新日志 {log_id} 失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"服务器错误: {str(e)}",
                "error": "SERVER_ERROR"
            }), 500

    @app.route('/api/logs/del', methods=['GET'])
    def delete_logs():
        try:
            log_id = request.args.get('id', type=int)
            if not log_id:
                return jsonify({"success": False, "message": "未指定要删除的日志"}), 400
            
            query = "DELETE FROM qso_log WHERE id = %s"
            execute_query(query, (log_id,))
            return jsonify({"success": True, "message": "日志删除成功"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    @app.route('/api/history/<callsign>', methods=['GET'])
    def get_history_by_callsign(callsign):
        try:
            query = """
            SELECT date, time, frequency, mode 
            FROM qso_log 
            WHERE callsign = %s
            ORDER BY date DESC, time DESC
            LIMIT 10
            """
            history = execute_query(query, (callsign,), fetch=True)
            return jsonify({
                "success": True,
                "data": history
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e),
                "error": "DATABASE_ERROR"
            }), 500
