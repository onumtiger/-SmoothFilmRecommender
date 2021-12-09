import firebase_admin 
from firebase_admin import firestore
firestore_db = firestore.client()

###
# Movie class: define movie object to add a new movie to the db
###

## movie without keywords
class newMovie(object):
    def __init__(self, movieId, name, actresses, genre, platforms, languages, rating, adult):
        self.movieId = movieId
        self.actresses = actresses
        self.genre = genre
        self.platforms = platforms
        self.languages = languages
        self.rating = rating
        self.name = name
        self.adult = adult
        self.playcount = 1
        self.userRating = 0

    @staticmethod
    def from_dict(source):
        # [START_EXCLUDE]
        movie = newMovie(source[u'movieId'], source[u'name'], source[u'actresses'], source[u'genre'], source[u'platforms'], source[u'languages'], source[u'rating'], source[u'adult'])

        if u'movieId' in source:
            movie.movieId = source[u'movieId']
        
        if u'name' in source:
            movie.name = source[u'name']
        
        if u'actresses' in source:
            movie.actresses = source[u'actresses']
        
        if u'genre' in source:
            movie.genre = source[u'genre']
        
        if u'platforms' in source:
            movie.platforms = source[u'platforms']

        if u'languages' in source:
            movie.languages = source[u'languages']
        
        if u'rating' in source:
            movie.rating = source[u'rating']

        if u'adult' in source:
            movie.adult = source[u'adult']
        
        return movie
        # [END_EXCLUDE]

    def to_dict(self):
        # [START_EXCLUDE]
        dest = {
            u'movieId': self.movieId,
            u'name': self.name,
            u'actresses': self.actresses,
            u'genre': self.genre,
            u'platforms': self.platforms,
            u'languages': self.languages,
            u'rating': self.rating,
            u'adult': self.adult,
            u'playcount': self.playcount,
            u'userRating': self.userRating

        }

        if self.movieId:
            dest[u'movieId'] = self.movieId

        if self.name:
            dest[u'name'] = self.name

        if self.actresses:
            dest[u'actresses'] = self.actresses
        
        if self.genre:
            dest[u'genre'] = self.genre

        if self.platforms:
            dest[u'platforms'] = self.platforms
        
        if self.languages:
            dest[u'languages'] = self.languages

        if self.rating:
            dest[u'rating'] = self.rating

        if self.adult:
            dest[u'adult'] = self.adult

        if self.playcount:
            dest[u'playcount'] = self.playcount
        
        if self.userRating:
            dest[u'userRating'] = self.userRating

        return dest
        # [END_EXCLUDE]

## movie with keywords
# class newMovie(object):
#     def __init__(self, movieId, name, actresses, genre, keywords, platforms, languages, rating, adult):
#         self.movieId = movieId
#         self.actresses = actresses
#         self.genre = genre
#         self.platforms = platforms
#         self.languages = languages
#         self.keywords = keywords
#         self.rating = rating
#         self.name = name
#         self.adult = adult
#         self.playcount = 1

#     @staticmethod
#     def from_dict(source):
#         # [START_EXCLUDE]
#         movie = newMovie(source[u'movieId'], source[u'name'], source[u'actresses'], source[u'genre'], source[u'keywords'], source[u'platforms'], source[u'languages'], source[u'rating'], source[u'playcount'])

#         if u'movieId' in source:
#             movie.movieId = source[u'movieId']

#         if u'name' in source:
#             movie.name = source[u'name']

#         if u'actresses' in source:
#             movie.actresses = source[u'actresses']

#         if u'genre' in source:
#             movie.genre = source[u'genre']

#         if u'keywords' in source:
#             movie.keywords = source[u'keywords']
    
#         if u'platforms' in source:
#             movie.platforms = source[u'platforms']

#         if u'languages' in source:
#             movie.languages = source[u'languages']

#         if u'rating' in source:
#             movie.rating = source[u'rating']

#         if u'adult' in source:
#             movie.adult = source[u'adult']

#         if u'playcount' in source:
#             movie.playcount = source[u'playcount']

#         return movie
#         # [END_EXCLUDE]

#     def to_dict(self):
#         # [START_EXCLUDE]
#         dest = {
#             u'movieId': self.movieId,
#             u'name': self.name,
#             u'actresses': self.actresses,
#             u'genre': self.genre,
#             u'keywords': self.keywords,
#             u'platforms': self.platforms,
#             u'languages': self.languages,
#             u'rating': self.rating,
#             u'adult': self.adult,
#             u'playcount': self.playcount
#         }

#         if self.movieId:
#             dest[u'movieId'] = self.movieId

#         if self.name:
#             dest[u'name'] = self.name

#         if self.actresses:
#             dest[u'actresses'] = self.actresses

#         if self.genre:
#             dest[u'genre'] = self.genre

#         if self.keywords:
#             dest[u'keywords'] = self.keywords

#         if self.platforms:
#             dest[u'platforms'] = self.platforms

#         if self.languages:
#             dest[u'languages'] = self.languages

#         if self.rating:
#             dest[u'rating'] = self.rating

#         if self.adult:
#             dest[u'adult'] = self.adult

#         if self.playcount:
#             dest[u'playcount'] = self.playcount

#         return dest
#         # [END_EXCLUDE]

###
# add movie to db
###
def add_movie(movie):
    print("add_movie")
    firestore_db = firestore.client()
    movies_ref = firestore_db.collection(u'Movies')
    print(movie.name)
    movies_ref.document(u'{}'.format(movie.movieId)).set(movie.to_dict())

###
# getter functions
###

def check_movie_exists_by_id(movieId):
    print("check_movie_exists_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        print('Document data: {}'.format(doc.to_dict()))
        return True
    else:
        print(u'No such document!')
        return False

def get_movie_by_id(movieId):
    print("get_movie_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        movie = doc.to_dict()
        return movie
    else:
        return 'No Movie found!'

def get_playcount_by_id(movieId):
    print("get_playcount_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return int(format(doc.to_dict()[u'playcount']))
    else:
        return 'No Movie found!'

def get_languages_by_id(movieId):
    print("get_languages_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'languages'])
    else:
        return 'No Movie found!'

def get_actresses_by_id(movieId):
    print("get_actresses_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'actresses'])
    else:
        return 'No Movie found!'

def get_genre_by_id(movieId):
    print("get_genre_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'genre'])
    else:
        return 'No Movie found!'

def get_platforms_by_id(movieId):
    print("get_platforms_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[u'platforms']
    else:
        return 'No Movie found!'

def get_keywords_by_id(movieId):
    print("get_keywords_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'keywords'])
    else:
        return 'No Movie found!'

def get_rating_by_id(movieId):
    print("get_rating_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return float(format(doc.to_dict()[u'rating']))
    else:
        return 'No Movie found!'

def get_user_rating_by_id(movieId):
    print("get_user_rating_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return int(format(doc.to_dict()[u'userRating']))
    else:
        return 'No Movie found!'

def get_adult_by_id(movieId):
    print("get_rating_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[u'adult']
    else:
        return 'No Movie found!'

def get_name_by_id(movieId):
    print("get_name_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'name'])
    else:
        return 'No Movie found!'

###
# setter functions
###

def increase_playcount(movieId):
    print("increase_playcount")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        count = int(format(doc.to_dict()[u'playcount']))
        count += 1
        doc_ref.update({u'playcount': count})
    else:
        return 'No Movie found!'

## increases or decreases the userRating by 1
def rate_movie(movieId, rating):
    print("rate_movie")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Movies').document(u'{}'.format(movieId))

    doc = doc_ref.get()
    if doc.exists:
        userRating = int(format(doc.to_dict()[u'userRating']))
        if rating == 1:
            userRating += 1
        if rating == 0:
            userRating -= 1
        print("new rating %s"%(userRating))
        doc_ref.update({u'userRating': userRating})
    else:
        return 'No Movie found!'
