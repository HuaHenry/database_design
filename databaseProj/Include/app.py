from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy  # 导入扩展类
from datetime import timedelta
import os
import sys
import hashlib
import requests
import json

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

# 创建Flask对象app并初始化
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + \
    os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
# 通过python装饰器的方法定义路由地址

# session
# session = requests.session()
app.secret_key = os.urandom(24)  # 随机生成session密钥
app.permanent_session_lifetime = timedelta(minutes=60)  # 设置session时效为60分钟

"""
    定义数据库模型
"""

# 用户信息表
class User(db.Model):  # 表名将会是 user（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)    # 主键
    name = db.Column(db.String(20))                 # 名字
    password = db.Column(db.String(20))             # 密码

# 风力信息表，包含经纬度、风速、风向、更新时间、是否展示
class Wind(db.Model):  # 表名将会是 wind（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)    # 主键
    latitude = db.Column(db.Float)                  # 纬度
    longitude = db.Column(db.Float)                 # 经度
    speed = db.Column(db.Float)                     # 风速
    direction = db.Column(db.Float)                 # 风向
    sea = db.Column(db.String(10))                  # 海域
    time = db.Column(db.String(20))                 # 更新时间
    show = db.Column(db.Boolean)                    # 是否展示

# 风力基站数据表
class Station(db.Model):  # 表名将会是 station（自动生成，小写处理）
    id = db.Column(db.Integer, primary_key=True)    # 主键
    latitude = db.Column(db.Float)                  # 纬度
    longitude = db.Column(db.Float)                 # 经度
    sea = db.Column(db.String(10))                  # 海域
    depth = db.Column(db.Float)                     # 深度
    pH = db.Column(db.Float)                        # 酸碱度
    
"""
    定义页面和方法
"""


@app.route("/")
# 定义方法 用jinjia2引擎来渲染页面，并返回一个index.html页面
def root():
    if 'name' not in session:
        return render_template("index.html", Username="")
    else:
        return render_template("index.html", Username=session['name'])


@app.route("/login")
# 定义方法 用jinjia2引擎来渲染页面，并返回一个index.html页面
def login():
    return render_template("login.html")

@app.route("/register")
# 定义方法 用jinjia2引擎来渲染页面，并返回一个index.html页面
def register():
    return render_template("register.html")

@app.route("/power")
# 定义方法 用jinjia2引擎来渲染页面，并返回一个index.html页面
def power():
    return render_template("power.html")

@app.route("/charts")
# 定义方法 用jinjia2引擎来渲染页面，并返回一个index.html页面
def charts():
    return render_template("charts.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/admin_site")
def admin_site():
    return render_template("admin_site.html")

@app.route("/admin_wind")
def admin_wind():
    return render_template("admin_wind.html")

@app.route("/admin_user")
def admin_user():
    return render_template("admin_user.html")

# app的路由地址"/submit"即为ajax中定义的url地址，采用POST、GET方法均可提交


@app.route("/reg_submit", methods=["GET", "POST"])
# 从这里定义具体的函数 返回值均为json格式
def submit():
    # 由于POST、GET获取数据的方式不同，需要使用if语句进行判断
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
    # if request.method == "GET":
    #     name = request.args.get("name")
    #     age = request.args.get("age")
    # 如果获取的数据为空
    print(name, password)
    if len(name) == 0 or len(password) == 0:
        return jsonify({"message": "error!"})
    else:
        # 首先查询用户名是否重复（用户名为系统的唯一凭证）
        if User.query.filter_by(name=name).first() is not None:
            return jsonify({"message": "已存在用户名，请重试!"})
        # 没有重复用户名，插入表项
        salt = name         # 把用户名作为盐值
        pw_salt = password + salt
        pw_md5 = hashlib.md5(pw_salt.encode()).hexdigest()
        user_tmp = User(name=name, password=pw_md5)
        db.session.add(user_tmp)
        db.session.commit()
        return jsonify({"message": "success!", "name": name})


@app.route("/login_submit", methods=["GET", "POST"])
def login_submit():
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
    if len(name) == 0 or len(password) == 0:
        return jsonify({"message": "error!"})
    else:
        user = User.query.filter_by(name=name).first()
        if user is None:
            return jsonify({"message": "用户名不存在!"})
        salt = name
        pw_salt = password + salt
        pw_md5 = hashlib.md5(pw_salt.encode()).hexdigest()
        if user.password == pw_md5:
            session.permanent = True  # 设置session为永久有效
            session['name'] = name
            return jsonify({"message": "success!", "name": name})
        else:
            return jsonify({"message": "密码错误!"})

# 查询风力信息
@app.route("/check_power", methods=["GET", "POST"])
def check_power():
    # 从请求中获取海域
    sealist = ["选择海域","中国黄海", "中国东海", "中国南海", "中国渤海"]
    sea_area = request.args.get("sea")
    sea_area = int(sea_area)
    print("查询海域为：", sealist[sea_area])
    if sea_area is None:
        return jsonify({"message": "error!"})
    # sea_area = "中国" + sea_area
    # 查询风力信息：海域匹配且show为True
    wind = Wind.query.filter_by(sea=sealist[sea_area], show=True).all()
    print(wind)
    # 将wind手动序列化为json
    wind_json = [{"latitude": w.latitude, "longitude": w.longitude, "speed": w.speed, "direction": w.direction, "time": w.time} for w in wind]
    print("查询到的风力信息：",wind_json)
    return wind_json

# 查询所有风力信息
@app.route("/check_all_power", methods=["GET", "POST"])
def check_all_power():
    # 查询风力信息：show为True
    wind = Wind.query.all()
    print(wind)
    # 将wind手动序列化为json
    wind_json = [{"latitude": w.latitude, "longitude": w.longitude, "speed": w.speed,"sea":w.sea, "direction": w.direction, "time": w.time,"show":w.show} for w in wind]
    print("查询到的风力信息：",wind_json)
    return wind_json

# 更新风力数据
@app.route("/edit_power", methods=["GET", "POST"])
def edit_power():
    # 接收数据
    data_edit = request.args.get("dataEdit")
    print("获取到的数据为",data_edit)
    # 解析数据为变量
    data_edit = json.loads(data_edit)
    longitude = data_edit["longitude"]
    latitude = data_edit["latitude"]
    sea_area = data_edit["sea"]
    speed = data_edit["speed"]
    direction = data_edit["direction"]
    time = data_edit["time"]
    show = data_edit["show"]
    # 更新wind数据表
    # 搜索数据表中经纬度匹配的数据
    wind = Wind.query.filter_by(latitude=latitude, longitude=longitude).first()
    wind.latitude = latitude
    wind.longitude = longitude
    wind.sea = sea_area
    wind.speed = speed
    wind.direction = direction
    wind.time = time
    wind.show = show
    db.session.commit()
    return "success!"

# 查询风力基站
@app.route("/check_station", methods=["GET", "POST"])
def check_station():
    # 查询风力信息：海域匹配且show为True
    site = Wind.query.filter_by(show=True).all()
    print(site)
    # 将wind手动序列化为json
    site_json = [{"latitude": w.latitude, "longitude": w.longitude, "sea_area":w.sea } for w in site]
    print("查询到的基站信息：",site_json)
    return site_json

# 查询station表获取基站详细信息
@app.route("/station_info", methods=["GET", "POST"])
def station_info():
    # 查询station表，返回所有基站信息
    site = Station.query.all()
    print(site)
    # 将site手动序列化为json
    return jsonify([{"id":w.id ,"latitude": w.latitude, "longitude": w.longitude, "sea_area":w.sea, "depth":w.depth, "pH":w.pH } for w in site])

# 百度文心api调用对话实现
API_KEY = "3v6bXvhkGJckDiwpdFqvYcP2"
SECRET_KEY = "B20oaVaMThEd8n1ZicfP1PSmx0rsXX24"
 
def Wenxin_chat(prompt):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie_speed?access_token=" + get_access_token()
    while(1):
        # 注意message必须是奇数条
        payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
        })
        headers = {
            'Content-Type': 'application/json'
        }
        res = requests.request("POST", url, headers=headers, data=payload).json()
        print(res)
        return res["result"]
 
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

# 获取百度文心接口实现对话式评估
@app.route("/evaluate", methods=["GET", "POST"])
def evaluate():
    # 获取前端传来的station id
    id = request.args.get("station_id")
    print(id)
    # 查询station表，返回所有基站信息
    site = Station.query.filter_by(id=id).first()
    latitude = site.latitude
    longitude = site.longitude
    sea_area = site.sea
    depth = site.depth
    pH = site.pH
    # 生成文心一言的输入pompt
    prompt = "现在有一个海洋风力基站，纬度为{}，经度为{}，海域为{}，海洋深度为{}，周围海水酸碱度为{}。请评估一下该地建设海洋风电场的环境可行性、经济可行性、优点和缺点。你的回答信息应该更关注于我给你的数据".format(latitude, longitude, sea_area, depth, pH)
    ans = Wenxin_chat(prompt)
    return ans

# 新增站点数据
@app.route("/add_site", methods=["GET", "POST"])
def add_site():
    # 接收数据
    data_add = request.args.get("dataAdd")
    print("获取到的数据为",data_add)
    # 解析数据为变量
    data_add = json.loads(data_add)
    longitude = data_add["longitude"]
    latitude = data_add["latitude"]
    sea_area = data_add["sea_area"]
    pH = data_add["pH"]
    depth = data_add["depth"]
    # 插入station数据表
    site = Station(latitude=latitude, longitude=longitude, sea=sea_area, pH=pH, depth=depth)
    db.session.add(site)
    db.session.commit()
    return "success!"

# 更新站点数据
@app.route("/edit_site", methods=["GET", "POST"])
def edit_site():
    # 接收数据
    data_edit = request.args.get("dataEdit")
    print("获取到的数据为",data_edit)
    # 解析数据为变量
    data_edit = json.loads(data_edit)
    id = data_edit["id"]
    longitude = data_edit["longitude"]
    latitude = data_edit["latitude"]
    sea_area = data_edit["sea_area"]
    pH = data_edit["pH"]
    depth = data_edit["depth"]
    # 更新station数据表
    site = Station.query.filter_by(id=id).first()
    site.latitude = latitude
    site.longitude = longitude
    site.sea = sea_area
    site.pH = pH
    site.depth = depth
    db.session.commit()
    return "success!"

# 删除站点数据
@app.route("/delete_site", methods=["GET", "POST"])
def delete_site():
    # 接收数据
    data_delete = request.args.get("dataDelete")
    print("获取到的数据为",data_delete)
    # 删除station数据表
    site = Station.query.filter_by(id=data_delete).first()
    db.session.delete(site)
    db.session.commit()
    return "success!"
    
# 定义app在8080端口运行
app.debug = True
app.run(port=8080)



