import pymysql


class Database:
    # 设置数据库的连接参数，由于我是在服务器中编写的，所以host是localhost
    host = "localhost"
    user = "root"
    password = "Hzq0307210"
    # 类的构造函数，参数db为欲连接的数据库。该构造函数实现了数据库的连接

    def __init__(self, db):
        connect = pymysql.connect(
            host=self.host, user=self.user, password=self.password, database=db)
        self.cursor = connect.cursor()
    # 类的方法，参数command为sql语句

    def execute(self, command):
        try:
            # 执行command中的sql语句
            self.cursor.execute(command)
        except Exception as e:
            return e
        else:
            # fetchall()返回语句的执行结果，并以元组的形式保存
            return self.cursor.fetchall()
