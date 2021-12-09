import pandas as pd
import firebase_admin

from firebase_admin import credentials, firestore
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

users = list(firestore_db.collection(u'Users').stream())
movies = list(firestore_db.collection(u'Movies').stream())

users_dict = list(map(lambda x: x.to_dict(), users))
movies_dict = list(map(lambda x: x.to_dict(), movies))

user_df = pd.DataFrame(users_dict)
movie_df = pd.DataFrame(movies_dict)

def recommendMovieFromGenre(userId):
   #get liked genre from userId
    filtered = user_df[user_df["userId"] == userId]
    genre = filtered["likedGenre"].item()

    #TODO convert genre to genreID
    genreId = 28

    #get recommendation from genre
    filtered = movie_df[movie_df["genre"] == genreId]
    sorted_df = filtered.sort_values(['userRating', 'rating', 'playcount'], ascending=[False, False, False])
    print(sorted_df.iloc[0])
    
    #TODO wie soll Element zurück gegeben werden?
    