from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import json
import random


# 验证码发送函数
def send_sms(template, phone):
    client = AcsClient('ALIYUN KEY', 'ALIYUN PASSWORD', 'default')
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('dysmsapi.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('http')  # https | http
    request.set_version('2017-05-25')

    # set_action_name 这个是选择你调用的接口的名称，如：SendSms，SendBatchSms等
    request.set_action_name('SendSms')
    # request.set_action_name('QuerySendDetails')

    # 这个参数也是固定的
    request.add_query_param('RegionId', "default")  # 98A66994-3DF4-4FA5-A33F-CCB36EB599D0
    # request.add_query_param('RegionId', "cn-hangzhou")

    request.add_query_param('PhoneNumbers', phone)  # 发给谁
    request.add_query_param('SignName', "你的签名")  # 签名
    request.add_query_param('TemplateCode', '你的模板')  # 模板编号
    request.add_query_param('TemplateParam', json.dumps({"code": template}))  # 发送验证码内容
    response = client.do_action_with_exception(request)
    return response


# 预约服务短信发送函数
def send_booking(phone):
    client = AcsClient('ALIYUN KEY', 'ALIYUN PASSWORD', 'default')
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain('dysmsapi.aliyuncs.com')
    request.set_method('POST')
    request.set_protocol_type('http')  # https | http
    request.set_version('2017-05-25')

    # set_action_name 这个是选择你调用的接口的名称，如：SendSms，SendBatchSms等
    request.set_action_name('SendSms')
    # request.set_action_name('QuerySendDetails')

    # 这个参数也是固定的
    request.add_query_param('RegionId', "default")  # 98A66994-3DF4-4FA5-A33F-CCB36EB599D0
    # request.add_query_param('RegionId', "cn-hangzhou")

    request.add_query_param('PhoneNumbers', phone)  # 发给谁
    request.add_query_param('SignName', "你的签名")  # 签名
    request.add_query_param('TemplateCode', '你的模板')  # 模板编号
    response = client.do_action_with_exception(request)
    return response


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 数据库配置信息
HOSTNAME = 'localhost'
PORT = '3306'
USERNAME = 'root'
PASSWORD = 'PASSWORD'
DATABASE = 'app'
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATABASE)
SQLALCHEMY_DATABASE_URI = DB_URI
# 设置SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()

#用户模型（基本信息表、健康状况表、费用表）
class Usermodel(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    childphone = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    sex = db.Column(db.String(255), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=False, unique=True)
    account = db.Column(db.Integer, nullable=False, unique=True)
    accountcost = db.Column(db.Integer, nullable=False, unique=True)


class ConditionsModel(db.Model):
    __tablename__ = "conditions"
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    BMI = db.Column(db.Float, nullable=False)
    BloodGlucose = db.Column(db.Float, nullable=False)
    systolic_pressure = db.Column(db.Float, nullable=False)
    diastolic_pressure = db.Column(db.Float, nullable=False)
    BloodFat = db.Column(db.Float, nullable=False)
    DiseasesHistory = db.Column(db.String(255), nullable=False)
    weight = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)


class CostModel(db.Model):
    __tablename__ = "cost"
    cost_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), db.ForeignKey('users.name'))
    cost = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    howcost = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    servicetype = db.Column(db.String(255), nullable=False)
    childphone = db.Column(db.String(255), nullable=False)

#初始化
db.init_app(app)


@app.route('/')
def index():
    return render_template('login.html')


def verify_user(username, password):
    user = Usermodel.query.filter_by(username=username).first()
    if user.password == password:
        return True
    return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            user = Usermodel.query.filter_by(username=username).first()
            session['use_id'] = user.id
            return redirect(url_for('show_success'))
        else:
            flash('登录失败，请检查您的用户名和密码是否正确。')
    return render_template('login.html')


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/send_code', methods=['GET'])
def send_code():
    phone = request.args.get('phone', '')
    print(f"Received phone: {phone}")
    if not phone:
        flash('请提供手机号码。')
        return redirect(url_for('signup'))
    session['phone_number'] = phone
    verification_code = "".join(random.choices('0123456789', k=6))
    send_sms(verification_code, phone)
    session['verification_code'] = verification_code  # 存储验证码到会话
    return "验证码发送成功", 200  


@app.route('/verify_code', methods=['POST'])
def verify_code():
    code = request.json.get('code')
    expected_code = session.get('verification_code')

    if code and code == expected_code:
        session.pop('verification_code', None)
        phone = session.get('phone_number')
        user = Usermodel.query.filter_by(childphone=phone).first()
        session['use_id'] = user.id
        return redirect(url_for('show_success'))
    else:
        flash('验证码错误或已过期。')
        return redirect(url_for('signup'))


@app.route('/success')
def show_success():
    return render_template('success.html')


@app.route('/appointment_booking')
def appointment_booking():
    user_id = session.get('use_id')
    user_phone_all = Usermodel.query.filter_by(id=user_id).first()
    if user_phone_all:
        user_phone_info = {
            'phone': user_phone_all.childphone,
            'name': user_phone_all.name,
        }
    return render_template('appointment_booking.html', user_phone_info=user_phone_info)


@app.route('/send_appointment', methods=['POST'])
def send_appiontment():
    user_id = session.get('use_id')
    numcost = CostModel.query.count()
    user_phone_all = Usermodel.query.filter_by(id=user_id).first()
    if user_phone_all:
        phone = user_phone_all.childphone
        send_booking(phone)
        date = request.json.get('bookingDatetime')
        paymentMethod = request.json.get('paymentMethod')
        serviceType = request.json.get('serviceType')
        totalFee_str = request.json.get('totalFee')
        totalFee = int(totalFee_str.replace('元', ''))
        newcost = CostModel(cost_id=numcost + 1, name=user_phone_all.name, cost=totalFee, type='服务费', date=date,
                            howcost=paymentMethod, status='未完成', servicetype=serviceType,
                            childphone=user_phone_all.childphone)
        db.session.add(newcost)
        if user_phone_all.account < totalFee:
            user_phone_all.accountcost = user_phone_all.accountcost + totalFee
            db.session.commit()
        else:
            user_phone_all.account = user_phone_all.account - totalFee
            db.session.commit()
        return redirect(url_for('appointment_booking_all'))


@app.route('/appointment_booking_all')
def appointment_booking_all():
    user_id = session.get('use_id')
    user_all = Usermodel.query.filter_by(id=user_id).first()
    user_cost = CostModel.query.filter_by(name=user_all.name).all()
    user_order_info_list = []
    for item in user_cost:
        user_order_info = {
            'name': item.name,
            'servicetype': item.servicetype,
            'childphone': item.childphone,
            'cost': item.cost,
            'status': item.status,
            'paymentMethod': item.howcost,
            'date': item.date,
            'address': user_all.address,
        }
        user_order_info_list.append(user_order_info)
    return render_template('appointment_booking_all.html', user_order_info_list = user_order_info_list)


@app.route('/my_profile')
def my_profile():
    user_id = session.get('use_id')
    user_my_profile = Usermodel.query.filter_by(id=user_id).first()
    user_cost = CostModel.query.filter_by(name=user_my_profile.name).all()
    if user_my_profile:
        my_profile_info = {
            'user_id': user_my_profile.id,
            'name': user_my_profile.name,
            'age': user_my_profile.age,
            'sex': user_my_profile.sex,
            'address': user_my_profile.address,
            'account': user_my_profile.account,
            'accountcost': user_my_profile.accountcost,
        }
    if user_cost:
        user_cost_info_list = []
        for item in user_cost:
            user_cost_info = {
                'cost': item.cost,
                'item': item.type,
                'date': item.date,
                'howcost': item.howcost
            }
            user_cost_info_list.append(user_cost_info)

    return render_template('my_profile.html', my_profile_info=my_profile_info, user_cost_info_list=user_cost_info_list)


@app.route('/health_status')
def health_status():
    user_id = session.get('use_id')
    condition = ConditionsModel.query.get(user_id)
    user_condition = Usermodel.query.filter_by(id=user_id).first()
    if condition:
        health_info = {
            'BMI': condition.BMI,
            'BloodGlucose': condition.BloodGlucose,
            'systolic_pressure': condition.systolic_pressure,
            'diastolic_pressure': condition.diastolic_pressure,
            'BloodFat': condition.BloodFat,
            'DiseasesHistory': condition.DiseasesHistory,
            'name': user_condition.name,
            'age': user_condition.age,
            'weight': condition.weight,
            'height': condition.height,
            'score': condition.score,
        }
    return render_template('health_status.html', health_info=health_info)


@app.route('/health_teach')
def health_teach():
    return render_template('health_teach.html')


@app.route('/submit', methods=['POST'])
def submit():
    return redirect(url_for('submission_ok'))


@app.route('/ok')
def submission_ok():
    return '提交成功！'


if __name__ == '__main__':
    app.run(host='0.0.0.0')
