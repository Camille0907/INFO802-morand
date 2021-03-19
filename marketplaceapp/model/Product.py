from graphene import ObjectType, String, ID, Float


class Product(ObjectType):
    id = ID()
    entitle = String()
    imageRef = String()
    price = Float()
    weight = Float()
    sellerId = ID()

    def __init__(self, idDoc, productDict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = idDoc
        self.entitle = productDict['entitle']
        self.imageRef = productDict['imageRef']
        self.price = productDict['price']
        self.weight = productDict['weight']
        self.sellerId = productDict['sellerId']

