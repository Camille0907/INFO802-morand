from json import loads

import requests
from flask import Flask, render_template, request, make_response
from graphene import Schema
from zeep import Client

from .model.dbCommunication.dbCommunication import Query, Mutations

app = Flask(__name__)
schema = Schema(query=Query, mutation=Mutations)

# Config options
app.config.from_object('config')


@app.route('/')
@app.route('/index/')
def index():
    # All products infos
    result = schema.execute('{allProducts {entitle imageRef id}}')
    products = result.to_dict()['data']['allProducts']

    # User infos
    userInfos = getUserInfos()

    return render_template('index.html', isUserConnected=userInfos['connected'], userName=userInfos['firstName'],
                           products=products)


@app.route('/price/<product_id>')
def price(product_id):
    # Product infos
    result = schema.execute(
        'query getProduct($id: ID!) { product(idDoc: $id) {entitle imageRef price weight sellerId}}',
        variables={'id': product_id}, )
    product = result.to_dict()['data']['product']

    # User infos
    userInfos = getUserInfos()
    if not userInfos['connected']:
        distance = None
        deliveryCost = None
    else:
        distance = computeDeleveryDistance(userInfos['id'], product['sellerId'])
        deliveryCost = computeDeleveryCost(distance, product['weight'])

    return render_template('price.html', isUserConnected=userInfos['connected'], userName=userInfos['firstName'],
                           product=product, distance=distance, deliveryCost=deliveryCost)


@app.route('/connection/')
def connexion():
    userInfos = getUserInfos()
    if not userInfos['connected']:
        return render_template('connection.html', error=False)
    else:
        return index()


@app.route('/login/', methods=['POST', 'GET'])
def login():
    # User infos
    result = schema.execute('query getUser($uname: String!, $pwd: String!) '
                            '{ userByUserNameAndPassword(username: $uname, password: $pwd) {id firstName}}',
                            variables={'uname': request.form['username'], 'pwd': request.form['password']})
    user = result.to_dict()['data']['userByUserNameAndPassword']
    if user is not None:
        return setUserInfos(userId=user['id'], name=user['firstName'])
    else:
        return render_template('connection.html', error=True)


@app.route('/logout/')
def logout():
    return setUserInfos(connected=False)


@app.route('/registration/')
def registration():
    return render_template('registration.html', error=False)


@app.route('/register/', methods=['POST', 'GET'])
def register():
    result = schema.execute('query getUser($uname: String!) { userByUserName(username: $uname) {id}}',
                            variables={'uname': request.form['username']})
    user = result.to_dict()['data']['userByUserName']
    if user is None:
        return createUserAndLogIn(request.form)
    else:
        return render_template('registration.html', error=True)


def createUserAndLogIn(formContent):
    result = schema.execute('mutation userCreation($uname: String!, $pwd: String!, $fname: String!, $pcode: String!) { '
                            'createUser(username: $uname, password: $pwd, firstName:$fname, postcode:$pcode) {id firstName}}',
                            variables={'uname': formContent['username'], 'pwd': formContent['password'],
                                       'fname': formContent['firstName'], 'pcode': formContent['postcode']})
    newUser = result.to_dict()['data']['createUser']
    return setUserInfos(userId=newUser['id'], name=newUser['firstName'])


def getUserInfos():
    connectedUserID = request.cookies.get('connectedUserID')
    if not connectedUserID:
        return {'connected': False, 'firstName': None}

    return {'connected': True, 'id': connectedUserID, 'firstName': request.cookies.get('connectedUserName')}


def setUserInfos(connected=True, userId=None, name=None):
    if connected:
        res = make_response(render_template('logRedirection.html', login=True))
        res.set_cookie('connectedUserID', userId)
        res.set_cookie('connectedUserName', name)
    else:
        res = make_response(render_template('logRedirection.html', login=False))
        res.set_cookie('connectedUserID', '', max_age=0)
        res.set_cookie('connectedUserName', '', max_age=0)
    return res


def computeDeleveryDistance(buyerId, sellerId):
    buyer = schema.execute('query getUserPostcode($id: ID!) { userById(idDoc: $id) {postcode}}', variables={'id': buyerId})
    buyerPostcode = buyer.to_dict()['data']['userById']['postcode']
    seller = schema.execute('query getUserPostcode($id: ID!) { userById(idDoc: $id) {postcode}}', variables={'id': sellerId})
    sellerPostcode = seller.to_dict()['data']['userById']['postcode']

    url = 'https://api.distancematrix.ai/maps/api/distancematrix/json?' \
          'origins=' + buyerPostcode + ',France&destinations=' + sellerPostcode + ',France&key=' + app.config[
              'DISTANCE_MATRIX_TOKEN']
    response = requests.request("GET", url)
    return loads(response.text)['rows'][0]['elements'][0]['distance']['value'] / 1000


def computeDeleveryCost(distance, weight):
    client = Client('http://127.0.0.1:8000/?wsdl')
    result = client.service.deliveryCost(distance, weight)
    return result
