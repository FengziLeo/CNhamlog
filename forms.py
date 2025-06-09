
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
import datetime

class QSOForm(FlaskForm):
    callsign = StringField('呼号')
    time = StringField('时间')
    frequency = FloatField('频率(MHz)')
    mode = SelectField('模式', choices=[
        ('', '请选择模式'),
        ('SSB', 'SSB'),
        ('USB', 'USB'),
        ('DSB', 'DSB'),
        ('CW', 'CW'), 
        ('FM', 'FM'),
        ('SSTV', 'SSTV'),
        ('FT8', 'FT8'),
        ('FT4', 'FT4'),
        ('DIGITAL', '其他数字模式')
    ], default='FM')
    equipment = StringField('设备')
    antenna = StringField('天线')
    power = FloatField('功率(W)', validators=[NumberRange(min=0, max=2000)], default=0.0)
    date = DateField('日期', default=datetime.date.today)
    notes = TextAreaField('备注')
    dxcc = StringField('DXCC国家编号') 
    grid = StringField('网格坐标')
    province = StringField('省份/州')
    band = StringField('波段')
    qslcard = SelectField('QSL卡片状态', choices=[
        ('0', '未换卡'),
        ('1', 'Eyeball'),
        ('2', '已换卡')
    ], default='0')
