import os
# Don't forget to import request
from flask import Flask, render_template, jsonify,request
import sqlalchemy
import random
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow, pprint

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')

# When deployed to App Engine, the `GAE_ENV` environment variable will be
# set to `standard`
def get_connection():
    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the local socket interface for accessing Cloud SQL
        unix_socket = '/cloudsql/{}'.format(db_connection_name)
        engine_url = 'mysql+pymysql://{}:{}@/{}?unix_socket={}'.format(
            db_user, db_password, db_name, unix_socket)
        return engine_url
    else:
        # If running locally, use the TCP connections instead
        # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
        # so that your application can use 127.0.0.1:3306 to connect to your
        # Cloud SQL instance
        host = '127.0.0.1'
        engine_url = 'mysql+pymysql://{}:{}@{}/{}'.format(
            db_user, db_password, host, db_name)
        return engine_url

    # The Engine object returned by create_engine() has a QueuePool integrated
    # See https://docs.sqlalchemy.org/en/latest/core/pooling.html for more
    # information


    # engine = sqlalchemy.create_engine(engine_url, pool_size=3)

app = Flask(__name__)
url = get_connection()
app.config['SQLALCHEMY_DATABASE_URI'] = url
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Numbers(db.Model):
    __tablename__='numbers'
    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.Integer)
    modified = db.Column(db.Integer)
    random = db.Column(db.Float)

    def __init__(self, original, random):
        self.original = original
        # self.modified = modified
        self.random = random


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255))
    lname = db.Column(db.String(255))
    email = db.Column(db.String(255))

class Dog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))

    def __init__(self, name):
        self.name = name

class UsersSchema(ma.Schema):
    class Meta:
        fields = ('fname', 'lname', 'email')

user_schema = UsersSchema()
users_schema = UsersSchema(many=True)

class NumbersSchema(ma.Schema):
    class Meta:
        fields = ('id', 'original', 'modified', 'random')

number_schema = NumbersSchema()
numbers_schema= NumbersSchema(many=True)

class DogSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name')

dog_schema = DogSchema()
dogs_schema = DogSchema(many=True)

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/users')
def users():
    all_users = Users.query.all()
    result = users_schema.dump(all_users)
    return jsonify(result.data)

@app.route('/numbers', methods=['POST'])
def add_number():
    data = request.get_json(force=True)
    originalnum = data['original']
    # modified = data['modified']
    random = data['random']

    new_number = Numbers(original=originalnum, random=random)

    db.session.add(new_number)
    db.session.commit()

    return number_schema.jsonify(new_number)

@app.route('/numbers_mod/<id>', methods=['POST'])
def modify_number(id):
    number = Numbers.query.get(id)
    modifiedNum = (number.original * 3)
    randomNum = float(random.randint(0, 500))

    new_number = Numbers(original=modifiedNum, random=randomNum)

    db.session.add(new_number)
    db.session.commit()

    return number_schema.jsonify(new_number)

@app.route('/numbers', methods=['GET'])
def get_numbers():
    all_numbers = Numbers.query.all()
    result = numbers_schema.dump(all_numbers)
#     # return render_template('numbers.html', result=result)
    return jsonify(result.data)
#     # return "GET ALL NUMBERS"

@app.route('/numbers/<id>', methods=['GET'])
def number_detail(id):
    number = Numbers.query.get(id)
    return number_schema.jsonify(number)

@app.route('/numbers_last', methods=['GET'])
def get_last_number():
    test = Numbers.query.order_by(Numbers.id.desc()).first()
    result = number_schema.dump(test)

    return jsonify(result.data)

@app.route("/numbers/<id>", methods=["PUT"])
def number_update(id):
    number = Numbers.query.get(id)
    modified = request.json['modified']

    number.modified = modified

    db.session.commit()
    return number_schema.jsonify(number)

@app.route('/numbers/<id>', methods=['DELETE'])
def number_delete(id):
    number = Numbers.query.get(id)
    db.session.delete(number)
    db.session.commit()

    return number_schema.jsonify(number)

@app.route('/dog', methods=['GET'])
def get_dogs():
    all_dogs = Dog.query.all()
    result = dogs_schema.dump(all_dogs)
    return jsonify(result.data)


if __name__ == '__main__':
    app.run(debug=True)
