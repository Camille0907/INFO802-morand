from json import loads
from flask import Flask, render_template, request, make_response
from graphene import Schema
import mangopay
import requests
from mangopay import APIRequest
from mangopay.resources import NaturalUser, CardRegistration, DirectPayIn, Wallet
from mangopay.utils import Money
from zeep import Client

from .model.dbCommunication.dbCommunication import Query, Mutations

app = Flask(__name__)
schema = Schema(query=Query, mutation=Mutations)

# Config options
app.config.from_object('config')

mangopay.client_id = app.config['MANGOPAY']['clientid']
mangopay.apikey = app.config['MANGOPAY']['apikey']
handler = APIRequest(sandbox=True)


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


@app.route('/price/<product_id>/')
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
        totalPrice = None
        sellerWalletId = None
    else:
        sellerId = product['sellerId']
        distance = computeDeleveryDistance(userInfos['id'], sellerId)
        deliveryCost = computeDeleveryCost(distance, product['weight'])
        totalPrice = product['price'] + deliveryCost
        seller = schema.execute('query getUserWallet($id: ID!) { userById(idDoc: $id) {walletId}}',
                                variables={'id': sellerId})
        sellerWalletId = seller.to_dict()['data']['userById']['walletId']

    return render_template('price.html', isUserConnected=userInfos['connected'], userName=userInfos['firstName'],
                           product=product, distance=distance, deliveryCost=deliveryCost, totalPrice=totalPrice,
                           sellerWalletId=sellerWalletId)


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


@app.route('/cardRegistration/', methods=['POST', 'GET'])
def cardRegistration():
    userInfos = getUserInfos()
    buyer = schema.execute('query getUserManopayId($id: ID!) { userById(idDoc: $id) {mangoId}}',
                           variables={'id': userInfos['id']})
    mangoUserId = buyer.to_dict()['data']['userById']['mangoId']

    return mangoCardRegistration(userInfos, mangoUserId, request.form['sellerWalletId'], request.form['totalPrice'])


@app.route('/payment/<card_registration_id>/<order_price>/<seller_wallet_id>')
def payment(card_registration_id, order_price, seller_wallet_id):
    userInfos = getUserInfos()
    processPayment(card_registration_id, order_price, seller_wallet_id)
    return render_template('successfulTransaction.html', isUserConnected=userInfos['connected'],
                           userName=userInfos['firstName'])


@app.route('/personnalProducts/')
def personnalProducts():
    # User infos
    userInfos = getUserInfos()

    # Products sold by connectedUser
    result = schema.execute('query getProtuctsBySellerId($sellerId: ID!) {productsBySellerId(sellerId: $sellerId) '
                            '{entitle imageRef id}}', variables={'sellerId': userInfos['id']})
    products = result.to_dict()['data']['productsBySellerId']

    return render_template('personnalProduct.html', isUserConnected=userInfos['connected'],
                           userName=userInfos['firstName'],
                           products=products)


@app.route('/deleteProduct/<product_id>')
def deleteProduct(product_id):
    schema.execute('mutation productDeletion($idDoc: ID){ deleteProduct(idDoc: $idDoc) {id}}',
                   variables={'idDoc': product_id})
    return personnalProducts()


@app.route('/newProduct/')
def newProduct():
    # User infos
    userInfos = getUserInfos()
    return render_template('newProduct.html', isUserConnected=userInfos['connected'], userName=userInfos['firstName'])


@app.route('/addProduct/', methods=['POST', 'GET'])
def addProduct():
    userInfos = getUserInfos()
    schema.execute('mutation productCreation($entitle: String!, $imageRef: String!, $price: Float!,$weight: Float!, $sellerId: ID!) { '
                   'createProduct(entitle: $entitle, imageRef: $imageRef, price:$price, weight:$weight, sellerId:$sellerId) {id}}',
                   variables={'entitle': request.form['entitle'], 'imageRef': request.form['imageRef'],
                              'price': request.form['price'], 'weight': request.form['weight'], 'sellerId': userInfos['id']})
    return personnalProducts()


@app.route('/productModification/<product_id>')
def productModification(product_id):
    # User infos
    userInfos = getUserInfos()

    result = schema.execute('query getProduct($id: ID!) { product(idDoc: $id) {id entitle imageRef price weight}}',
                            variables={'id': product_id}, )
    product = result.to_dict()['data']['product']
    return render_template('productModification.html', isUserConnected=userInfos['connected'], userName=userInfos['firstName'],
                           product=product)


@app.route('/modifyProduct/<product_id>', methods=['POST', 'GET'])
def modifyProduct(product_id):
    schema.execute('mutation productModification($idDoc: ID!, $entitle: String!, $imageRef: String!, $price: Float!,$weight: Float!) { '
                   'modifyProduct(idDoc: $idDoc, entitle: $entitle, imageRef: $imageRef, price:$price, weight:$weight) {id}}',
                   variables={'idDoc': product_id, 'entitle': request.form['entitle'], 'imageRef': request.form['imageRef'],
                              'price': request.form['price'], 'weight': request.form['weight']})
    return personnalProducts()


def createUserAndLogIn(formContent):
    mangoUser = createMangoUser(formContent)
    walletId = createMangoWallet(mangoUser)
    result = schema.execute('mutation '
                            'userCreation($uname: String!, $pwd: String!, $fname: String!, $pcode: String!, '
                            '$mangoId: ID!, $walletId: ID!) { '
                            'createUser(username: $uname, password: $pwd, firstName:$fname, postcode:$pcode, '
                            'mangoId:$mangoId, walletId:$walletId) {id firstName}}',
                            variables={'uname': formContent['username'], 'pwd': formContent['password'],
                                       'fname': formContent['firstName'],
                                       'pcode': formContent['postcode'], 'mangoId': mangoUser.id, 'walletId': walletId})
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
    buyer = schema.execute('query getUserPostcode($id: ID!) { userById(idDoc: $id) {postcode}}',
                           variables={'id': buyerId})
    buyerPostcode = buyer.to_dict()['data']['userById']['postcode']
    seller = schema.execute('query getUserPostcode($id: ID!) { userById(idDoc: $id) {postcode}}',
                            variables={'id': sellerId})
    sellerPostcode = seller.to_dict()['data']['userById']['postcode']

    url = 'https://api.distancematrix.ai/maps/api/distancematrix/json?' \
          'origins=' + buyerPostcode + ',France&destinations=' + sellerPostcode + ',France&key=' + app.config[
              'DISTANCE_MATRIX_TOKEN']
    response = requests.request("GET", url)
    return loads(response.text)['rows'][0]['elements'][0]['distance']['value'] / 1000


def computeDeleveryCost(distance, weight):
    client = Client('https://deliverycostservice-morand.herokuapp.com/?wsdl')
    result = client.service.deliveryCost(distance, weight)
    return result


def mangoCardRegistration(userInfos, mangoUserId, sellerWalletId, orderPrice):
    mangoUser = NaturalUser.get(mangoUserId)

    # Card registration
    card_registration = CardRegistration(user=mangoUser, currency='EUR')
    card_registration.save()

    # It isn't a good solution to have the price in the url (this could be changed)
    # But the mangoPay redirection empeach the use of POST
    # The solution would be to stock the orders in the database, and to use an id in the url
    # But it isn't really interesting here...
    returnURL = request.url_root + 'payment/' + card_registration.id + '/' + orderPrice + '/' + sellerWalletId

    # Card number example (for orders under 50 euros): 4972485830400049
    return render_template('cardRegistration.html', isUserConnected=userInfos['connected'],
                           userName=userInfos['firstName'],
                           accessKeyRef=card_registration.access_key, data=card_registration.preregistration_data,
                           registrationUrl=card_registration.card_registration_url, returnURL=returnURL)


def createMangoUser(formContent):
    # Some infos are falsified to lighten the registration form
    # It isn't important here to create false users
    params = {
        "first_name": formContent['firstName'],
        "last_name": formContent['firstName'],
        "birthday": 1300186358,
        "nationality": "FR",
        "country_of_residence": "FR",
        "email": formContent['email'],
    }
    user = NaturalUser(**params)
    user.save()
    return user


def createMangoWallet(mangoUser):
    wallet = Wallet(owners=[mangoUser], description='SellerWallet', currency='EUR')

    wallet.save()
    return wallet.get_pk()


def processPayment(cardRegistrationId, orderPrice, sellerWalletId):
    # End of card registration
    card_registration = CardRegistration.get(cardRegistrationId)
    if card_registration.registration_data is None:
        card_registration.registration_data = request.args.get('data')
        card_registration.save()

    # The card registration doesn't seems to create a card...
    # The pay can't work without

    # Pay_in
    """
    returnURL = request.url_root + 'successfulTransaction/'
    card = card_registration.card
    cardId = card_registration.card_id
    direct_payin = DirectPayIn(author=card.user,
                               debited_funds=Money(amount=orderPrice, currency='EUR'),
                               fees=Money(amount=0, currency='EUR'),
                               credited_wallet_id=sellerWalletId,
                               card_id=cardId,
                               secure_mode_return_url=returnURL)
    direct_payin.save()
    """
