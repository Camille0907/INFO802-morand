Camille Morand 

# TP : Marketplace

Le TP est réalisé intégralement en Python, avec l'aide du micro-framework Flask.

Le déploiement du site web et du service SOAP ont tous les deux été faits sur Heroku.

<a href=https://marketplace-morand.herokuapp.com/> Lien vers l'application Market Place.</a>

<a href=https://deliverycostservice-morand.herokuapp.com/?wsdl> Lien vers le WSDL du service SOAP.</a>

- Partie Soap : le service SOAP expose une seule fonction, qui prend une distance et un poids en paramètres, et retourne les frais de livraison. Le client réussit à l'interroger pour se servir de ce qu'il retourne.

- Communication avec la BDD: on utilise ici Firestore, et on communique avec elle via la librairie prévue.

- Partie GraphQL : Firestore ne proposant pas de communiquer en utilisant GraphQL (ou je n'ai pas su trouvé), le graphQL codé ici est interne au serveur: il permet à la vue de demander les informations dont elle a besoin au modèle. Celui-ci interroge Firebase puis répond avec GraphQL. La librairie utilisée est Graphene Python. On remarquera que la communication de cette façon en interne du serveur n'a pas vraiment d'intérêt, en particulier cela ne met pas en valeur l'intérêt de graphQL de récupérer seulement les données souhaitées. Cela a cependant permis de bien comprendre son fonctionnement. Le site propose d'accéder à la base de données en lecture (utilisateurs et produits entre autres), et en écriture (inscription d'utilisateurs, création/modification/suppression de produits), pour balayer différents types de requêtes. Toutes les requêtes implémentées fonctionnent.

- Partie MangoPay : On utilise l'API proposée par le site, qui abstrait la communication en REST, bien qu'une grande partie de la documentation à utiliser concerne REST. Ainsi le fonctionnement de REST pourrait être expliqué, malgré l'utilisation de l'API. Une partie n'a pas été réalisée: l'enregistrement d'un CardRegistration est censé créer un Card, indispensable à la transaction, mais n'a jamais fonctionné. Pour autant, tout ce qui est nécessaire à un paiement est codé, mais la dernière étape est commentée: c'est la seule qui ne fonctionne pas.

- Partie REST : une autre API REST est utilisée, il s'agit de DistanceMatrix.ai, qui permet de récupérer une distance entre deux lieux, en particulier pour ce site entre deux code postaux. Là aucune API n'est utilisée, l'interrogation se fait directement en REST. 

- Partie web: tout le reste du TP, en particulier la gestion d'erreur ou l'aspect visuel, sont traités au minimum pour faire tourner le site: un usage de boutons de navigation du navigateur, ou l'écriture de données au  mauvais format dans les formulaire par exemple pourraient compromettre le fonctionnement du site.
