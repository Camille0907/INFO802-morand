from graphene import ObjectType, String, ID, Int


class User(ObjectType):
    id = ID()
    username = String()
    password = String()
    firstName = String()
    postcode = String()

    def __init__(self, idDoc, userDict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = idDoc
        self.username = userDict['username']
        self.password = userDict['password']
        self.firstName = userDict['firstName']
        self.postcode = userDict['postcode']

