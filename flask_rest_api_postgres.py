import json
import uuid  # for public id
from datetime import datetime, timedelta
from functools import wraps
import jwt

# imports for PyJWT authentication
from db_config import local_session
from db_repo import DbRepo
from tables.users import Users
from tables.customers import Customers
# flask imports
from flask import Flask, request, jsonify, make_response, Response
from logger import Logger
from werkzeug.security import generate_password_hash, check_password_hash

# creates Flask object
app = Flask(__name__)
repo = DbRepo(local_session)
logger = Logger.get_instance()
app.config['SECRET_KEY'] = 'your secret key'


def convert_to_json(_list: list):
    json_list = []
    for i in _list:
        _dict = i.__dict__
        _dict.pop('_sa_instance_state', None)
        json_list.append(_dict)
    return json_list

@app.route("/")
def home():
    print('hi')
    return '''
        <html>
            Customers And Users
        </html>
    '''
# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            token = token.removeprefix('Bearer ')
            # return 401 if token is not passed
        if not token:
            logger.logger.error(f'Token is missing, error 401')
            return jsonify({'message': 'Token is missing !!'}), 401
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = repo.update_by_column_value(Users, Users.public_id, data['public_id'], data['public_id']).first()
        except:
            return jsonify({'message': 'Token is invalid !!'}), 401

        # passes the current logged in user into the endpoint so
        # you have access to them
        # (you also just pass the data of the token, or whatever
        #  you want)
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/customers', methods=['GET', 'POST'])
def get_or_post_customers():
    if request.method == 'GET':
        return jsonify(convert_to_json(repo.get_all_customers()))
    if request.method == 'POST':
        customer_data = request.get_json()
        new_customer = convert_to_json([Customers(name=customer_data["name"], address=customer_data["address"])])
        repo.post_customer(new_customer)
        logger.logger.info(f'creating new customer {request.base_url}/{new_customer["id"]}')
        return Response(f'"new-item": "{request.base_url}"/"{new_customer["id"]}"', status = 201, mimetype = "application/json")

@app.route('/customers/<int:customer_id>', methods=['GET', 'PUT', 'DELETE', 'PATCH'])
def get_customer_by_id(customer_id):
    if request.method == 'GET':
        customer = repo.get_customer_by_id(customer_id)
        return jsonify(convert_to_json(customer))
    if request.method == 'PUT':
        customer = request.get_json()
        return repo.put_by_id(customer)
    if request.method == 'DELETE':
        return repo.delete_customer(customer_id)
    if request.method == 'PATCH':
        customer = convert_to_json(request.get_json())
        return repo.patch_by_id(customer)


@app.route('/customers', methods=['GET', 'POST'])
def get_or_post_customer_by_params():
    if request.method == 'GET':
        search_args = request.args.to_dict()
        customers = jsonify(repo.get_all_customers(search_args))
        if len(search_args) == 0:
            return make_response(jsonify(customers), status=200, mimetype='application/json')
        results = []
        for c in customers:
            if "name" in search_args.keys():
                if c["name"].find(search_args["name"]) < 0:
                    continue
            if "address" in search_args.keys() and c["address"].find(search_args["address"]) < 0:
                continue
            results.append(c)
        if len(results) == 0:
            return Response("[]", status=404, mimetype='application/json')
        return Response(jsonify(customers), status=200, mimetype='application/json')
    if request.method == 'POST':
        new_customer = request.get_json()
        repo.add(jsonify(new_customer))
        logger.logger.ino(f'creating new customer {request.base_url}/{new_customer["id"]}')
        return Response(f'"new-item": "{request.base_url}"/"{new_customer["id"]}"', status=201,
                        mimetype="application/json")


@app.route('/signup', methods=['POST'])
def signup():
    form_data = request.form
    # gets name, email and password from request
    _username = form_data.get('name')
    _email = form_data.get('email')
    _password = form_data.get('password')

    # check if user exists in db
    user = repo.get_user_by_username(_username)
    # ...
    if user:
        return make_response('User already exists. Please Log in.', 202)
    else:
        # create new user
        user = Users(public_id=str(uuid.uuid4()), username=_username, email=_email,
            password=generate_password_hash(_password))
        return make_response('Successfully registered.', 201)

@app.route('/login', methods=['POST'])
def login():
    form_data = request.form

    # check that no field is missing
    if not form_data.get('username') or not form_data.get('password'):
        return make_response('Could not verify', 401,
                             {'WWW-Authenticate': 'Basic realm ="Login required!"'})
    # check if user exists in db
    user = repo.get_user_by_username(form_data.get('username'))
    # ...

    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm ="User does not exist!"'})
    # check password
    if not check_password_hash(user[0].password, form_data.get('password')):
        return make_response('Could not verify', 403, {'WWW-Authenticate': 'Basic realm ="Wrong Password!"'})
    # generates the JWT Token
    token = jwt.encode({'public_id': user[0].public_id,'exp': datetime.utcnow() + timedelta(minutes=30)}, app.config['SECRET_KEY'])

    return make_response(jsonify({'token': token.decode('UTF-8')}), 201)

if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debuger shell
    # if you hit an error while running the server
    app.run(debug=True)
