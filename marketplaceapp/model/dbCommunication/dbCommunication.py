import firebase_admin
from firebase_admin import credentials, firestore
from graphene import ObjectType, List, Field, ID, String, Mutation

from ..Product import Product
from ..User import User

cred = credentials.Certificate("marketplaceapp/model/dbCommunication/serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


class CreateUser(Mutation):
    class Arguments:
        username = String()
        password = String()
        firstName = String()
        postcode = String()

    id = ID()
    firstName = String()

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = user.id
        self.firstName = user.firstName

    def mutate(root, info, username, password, firstName, postcode):
        new_user_doc = db.collection('users').document()
        new_user_data = {
            'username': username,
            'password': password,
            'firstName': firstName,
            'postcode': postcode
        }
        new_user_doc.set(new_user_data)
        user = User(new_user_doc.id, new_user_data)
        return CreateUser(user)


class Mutations(ObjectType):
    create_user = CreateUser.Field()


class Query(ObjectType):
    allProducts = List(Product)
    product = Field(Product, idDoc=ID(required=True))
    userByUserNameAndPassword = Field(User, username=String(required=True), password=String(required=True))
    userByUserName = Field(User, username=String(required=True))
    userById = Field(User, idDoc=ID(required=True))

    def resolve_allProducts(root, info):
        docs = db.collection('products').stream()
        res = list()
        for doc in docs:
            res.append(Product(doc.id, doc.to_dict()))
        return res

    def resolve_product(root, info, idDoc):
        doc_ref = db.collection('products').document(idDoc)

        doc = doc_ref.get()
        return Product(doc.id, doc.to_dict())

    def resolve_userByUserNameAndPassword(root, info, username, password):
        doc_ref = db.collection('users').where('username', '==', username).where('password', '==', password)
        docs = doc_ref.stream()
        res = list()
        for doc in docs:
            res.append(User(doc.id, doc.to_dict()))
        if len(res) == 0:
            return None
        return res[0]

    def resolve_userByUserName(root, info, username):
        doc_ref = db.collection('users').where('username', '==', username)
        docs = doc_ref.stream()
        res = list()
        for doc in docs:
            res.append(User(doc.id, doc.to_dict()))
        if len(res) == 0:
            return None
        return res[0]

    def resolve_userById(root, info, idDoc):
        doc_ref = db.collection('users').document(idDoc)
        doc = doc_ref.get()
        return User(doc.id, doc.to_dict())
