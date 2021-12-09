import firebase_admin 
from firebase_admin import firestore
firestore_db = firestore.client()

from movie_api_functions import getMovieID
from movie_firebase_functions import rate_movie

###
# User class: define user object to add a new user to the db
###
class User(object):
    def __init__(self, dislikedGenre, favouriteActress, favouriteMovie, userId, language, lastWatchedMovie, likedGenre, name, recommendedMovies, streamingPlatforms, likings, recommendAgain):
        self.dislikedGenre = dislikedGenre
        self.favouriteActress = favouriteActress
        if getMovieID(favouriteMovie) != 0:
            self.favouriteMovie = favouriteMovie
        else:
            self.favouriteMovie = "Joker"
        self.userId = userId
        self.language = language
        self.lastWatchedMovie = lastWatchedMovie
        self.likedGenre = likedGenre
        self.name = name
        self.recommendedMovies = recommendedMovies
        self.streamingPlatforms = streamingPlatforms
        self.likings= likings
        self.recommendAgain = recommendAgain

    @staticmethod
    def from_dict(source):
        # [START_EXCLUDE]
        user = User(source[u'dislikedGenre'], source[u'favouriteActress'], source[u'favouriteMovie'], source[u'userId'], source[u'language'], source[u'lastWatchedMovie'], source[u'likedGenre'], source[u'name'], source[u'recommendedMovies'], source[u'streamingPlatforms'], source[u'likings'], source[u'recommendAgain'])

        if u'dislikedGenre' in source:
            user.dislikedGenre = source[u'dislikedGenre']
        
        if u'favouriteActress' in source:
            user.favouriteActress = source[u'favouriteActress']
        
        if u'favouriteMovie' in source:
            user.favouriteMovie = source[u'favouriteMovie']
        
        if u'userId' in source:
            user.userId = source[u'userId']
        
        if u'language' in source:
            user.language = source[u'language']
        
        if u'lastWatchedMovie' in source:
            user.lastWatchedMovie = source[u'lastWatchedMovie']

        if u'likedGenre' in source:
            user.likedGenre = source[u'likedGenre']
        
        if u'name' in source:
            user.name = source[u'name']

        if u'recommendedMovies' in source:
            user.recommendedMovies = source[u'recommendedMovies']
        
        if u'streamingPlatforms' in source:
            user.streamingPlatforms = source[u'streamingPlatforms']

        return user
        # [END_EXCLUDE]

    def to_dict(self):
        # [START_EXCLUDE]
        dest = {
            u'dislikedGenre': self.dislikedGenre,
            u'favouriteActress': self.favouriteActress,
            u'favouriteMovie': self.favouriteMovie,
            u'userId': self.userId,
            u'language': self.language,
            u'lastWatchedMovie': self.lastWatchedMovie,
            u'likedGenre': self.likedGenre,
            u'name': self.name,
            u'recommendedMovies': self.recommendedMovies,
            u'streamingPlatforms': self.streamingPlatforms,
            u'likings': self.likings,
            u'recommendAgain': self.recommendAgain

        }

        if self.dislikedGenre:
            dest[u'dislikedGenre'] = self.dislikedGenre

        if self.favouriteActress:
            dest[u'favouriteActress'] = self.favouriteActress

        if self.favouriteMovie:
            dest[u'favouriteMovie'] = self.favouriteMovie
        
        if self.userId:
            dest[u'userId'] = self.userId

        if self.language:
            dest[u'language'] = self.language

        if self.lastWatchedMovie:
            dest[u'lastWatchedMovie'] = self.lastWatchedMovie
        
        if self.likedGenre:
            dest[u'likedGenre'] = self.likedGenre

        if self.name:
            dest[u'name'] = self.name

        if self.recommendedMovies:
            dest[u'recommendedMovies'] = self.recommendedMovies

        if self.streamingPlatforms:
            dest[u'streamingPlatforms'] = self.streamingPlatforms

        if self.likings:
            dest[u'likings'] = self.likings
        
        if self.recommendAgain:
            dest[u'recommendAgain'] = self.recommendAgain

        return dest
        # [END_EXCLUDE]

    # def __repr__(self):
    #     return(
    #         f'User(\
    #             dislikedGenre={self.dislikedGenre}, \
    #             favouriteActress={self.favouriteActress}, \
    #             favouriteMovie={self.favouriteMovie}, \
    #             userId={self.userId}, \
    #             language={self.language},\
    #             lastWatchedMovie={self.lastWatchedMovie}, \
    #             name={self.name}, \
    #             recommendedMovies={self.recommendedMovies}, \
    #             streamingPlatforms={self.streamingPlatforms} \
    #         )'
    #     )

###
# add user to db
###
def add_user(user):
    print("add_user")
    firestore_db = firestore.client()
    users_ref = firestore_db.collection(u'Users')
    # print(user.name)
    users_ref.document(u'{}'.format(user.userId)).set(user.to_dict())

####
## GETTER FUNCTIONS
####

## returns boolean
def check_user_exists_by_id(userId):
    print("check_user_exists_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        # print('Document data: {}'.format(doc.to_dict()))
        return True
    else:
        print(u'No such document!')
        return False

## returns user as dictionary
def get_user_by_id(userId):
    print("get_user_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        user = doc.to_dict()
        return user
    else:
        return 'No User found!'


## returns username as string
def get_username_by_id(userId):
    print("get_username_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        return format(doc.to_dict()[u'name'])
    else:
        return 'No User found!'


## returns streamingplattforms as array of strings
def get_streaming_platforms_by_id(userId):
    print("get_streaming_platforms_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[u'streamingPlatforms']
    else:
        print("No User found!")
        return []


## returns recommended movies as array of strings
def get_recommended_movies_by_id(userId):
    print("get_recommended_movies_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()[u'recommendedMovies']
    else:
        print("No User found!")
        return []


## returns last watched as string
def get_last_watched_movie_by_id(userId):
    print("get_last_watched_movie_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    lastWatchedMovie = doc.to_dict()[u'lastWatchedMovie']
    return format(lastWatchedMovie[0])


## returns bool
def is_last_watched_movie_rated_by_id(userId):
    print("is_last_watched_movie_rated_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    lastWatchedMovie = doc.to_dict()[u'lastWatchedMovie']
    return lastWatchedMovie[1]


## returns favourite actress as string
def get_favourite_actress_by_id(userId):
    print("get_favourite_actress_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        favouriteActress = format(doc.to_dict()[u'favouriteActress'])
        return favouriteActress
    else:
        return 'No User found!'


## returns favourite movie as string
def get_favourite_movie_by_id(userId):
    print("get_favourite_movie_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        favouriteMovie = format(doc.to_dict()[u'favouriteMovie'])
        return favouriteMovie
    else:
        return 'No User found!'


## returns language as string
def get_language_by_id(userId):
    print("get_language_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        language = format(doc.to_dict()[u'language'])
        return language
    else:
        print('No User found!')
        return ""


## returns disliked genres as array of strings
def get_disliked_genre_by_id(userId):
    print("get_disliked_genre_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        dislikedGenre = format(doc.to_dict()[u'dislikedGenre'])
        return dislikedGenre
    else:
        return 'No User found!'


## returns liked genre as array of strings
def get_liked_genre_by_id(userId):
    print("get_liked_genre_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        likedGenre = format(doc.to_dict()[u'likedGenre'])
        return likedGenre
    else:
        return 'No User found!'

## returns likings as dict
def get_likings_by_id(userId):
    print("get_likings_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        likings = doc.to_dict()[u'likings']
        return likings
    else:
        print('No User found!')
        return {}

def get_recommended_again_by_id(userId):
    print("get_recommended_again_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        likings = doc.to_dict()[u'recommendAgain']
        return likings
    else:
        print('No User found!')
        return []

####
## UPDATE FUNCTIONS
####

def update_recommended_movies_by_id(userId, movie):
    print("update_recommended_movies_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    recommendedMovies = doc.to_dict()[u'recommendedMovies']
    print("recommendedMovies")
    print(recommendedMovies)
    if recommendedMovies[0] == "":
        recommendedMovies[0] = movie
    else: 
        recommendedMovies.append(movie)
    doc_ref.update({u'recommendedMovies': recommendedMovies})

def update_recommended_again_by_id(userId, movie):
    print("update_recommended_again_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    recommendAgain = doc.to_dict()[u'recommendAgain']
    print("recommendAgain")
    print(recommendAgain)
    if recommendAgain[0] == "":
        recommendAgain[0] = movie
    else: 
        recommendAgain.append(movie)
    doc_ref.update({u'recommendAgain': recommendAgain})

def clear_recommended_again_by_id(userId):
    print("clear_recommended_again_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    recommendAgain = [""]
    doc_ref.update({u'recommendAgain': recommendAgain})

def update_last_watched_movie_by_id(userId, movie):
    print("update_last_watched_movie_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    lastWatchedMovie = doc.to_dict()[u'lastWatchedMovie']
    lastWatchedMovie[0] = movie
    lastWatchedMovie[1] = False
    doc_ref.update({u'lastWatchedMovie': lastWatchedMovie})

def update_disliked_genre(userId, genre):
    print("update_disliked_genre")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    dislikedGenre = doc.to_dict()[u'dislikedGenre']
    if dislikedGenre[0] == "":
        dislikedGenre[0] = genre
    else: 
        dislikedGenre.append(genre)
    doc_ref.update({u'dislikedGenre': dislikedGenre})

def update_favourite_actress(userId, actress):
    print("update_favourite_actress")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    doc_ref.update({u'favouriteActress': actress})

def update_favourite_movie(userId, movie):
    print("update_favourite_movie")
    if getMovieID(movie) != 0:
        firestore_db = firestore.client()
        doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
        doc = doc_ref.get()
        doc_ref.update({u'favouriteMovie': movie})

def update_language(userId, language):
    print("update_language")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    doc_ref.update({u'language': language})

def update_liked_genre(userId, genre):
    print("update_liked_genre")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    likedGenre = doc.to_dict()[u'likedGenre']
    if likedGenre[0] == "":
        likedGenre[0] = genre
    else: 
        likedGenre.append(genre)
    doc_ref.update({u'likedGenre': likedGenre})

def update_name(userId, name):
    print("update_name")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    doc_ref.update({u'name': name})

def update_streaming_platforms(userId, streamingPlatforms):
    print("update_streaming_platforms")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    platforms = doc.to_dict()[u'streamingPlatforms']
    if platforms[0] == "":
        platforms[0] = streamingPlatforms
    else: 
        platforms.append(streamingPlatforms)
    doc_ref.update({u'streamingPlatforms': platforms})


def rate_last_watched_movie_by_id(userId, rating):
    print("rate_last_watched_movie_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))
    doc = doc_ref.get()
    lastWatchedMovie = doc.to_dict()[u'lastWatchedMovie']
    lastWatchedMovie[1] = True
    movieId = getMovieID(lastWatchedMovie[0])
    rate_movie(movieId, rating)
    doc_ref.update({u'lastWatchedMovie': lastWatchedMovie})


## increase likings as dict
def update_likings_by_id(userId, likingsInput):
    print("update_likings_by_id")
    firestore_db = firestore.client()
    doc_ref = firestore_db.collection(u'Users').document(u'{}'.format(userId))

    doc = doc_ref.get()
    if doc.exists:
        likings = doc.to_dict()[u'likings']
        if likingsInput['acting']:
            likings['acting'] += 1
        if likingsInput['genre']:
            likings['genre'] += 1
        if likingsInput['movie']:
            likings['movie'] += 1
        doc_ref.update({u'likings': likings})
        print("new likings: %s" %(likings))
        return "likings increased"
    else:
        return 'No User found!'
