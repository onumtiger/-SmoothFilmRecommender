import pandas as pd
import firebase_admin

from movie_firebase_functions import *
from user_firebase_functions import *
from movie_api_functions import *

import operator
import random

from firebase_admin import firestore
firestore_db = firestore.client()

users = list(firestore_db.collection(u'Users').stream())
users_dict = list(map(lambda x: x.to_dict(), users))
user_df = pd.DataFrame(users_dict)

movies = list(firestore_db.collection(u'Movies').stream())
movies_dict = list(map(lambda x: x.to_dict(), movies))
movie_df = pd.DataFrame(movies_dict)

#filter database and get all movies with actor
def customRecommendMovieFromActress(userId, actressName):
    counter = 0
    stop = 0

    recommendedMovies = get_recommended_movies_by_id(userId)
    actressId = getActressId(actressName)

    movieSuggestions = pd.DataFrame(columns=['movieId','name', 'rating', 'userRating', 'playcount'])
    for index, row in movie_df.iterrows():
        if(row["actresses"].count(actressId)>0):
            movieSuggestions = movieSuggestions.append({'movieId': row["movieId"], 'name': row["name"]}, ignore_index=True)
    
    movieSuggestions = movieSuggestions.sort_values(['userRating', 'rating', 'playcount'], ascending=[False, False, False])
            
    if(movieSuggestions.empty):
        recommendation = {}
    else:
        availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]["movieId"])

        while not availableOn or getMovieName(movieSuggestions.iloc[counter]["movieId"]) in recommendedMovies:
            counter += 1
            if counter == len(movieSuggestions):
                stop = 1
                break
            availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]["movieId"])

        if (stop == 1):
            recommendation = {}
        else: 
            recommendation = { 'movieId': movieSuggestions.iloc[counter]["movieId"], 'titel': movieSuggestions.iloc[counter]['name'], 'platforms': availableOn}
            update_recommended_movies_by_id(userId, recommendation['titel'])
        
    print(recommendation)
    return recommendation

#filter database and get all movies with genre and sorted by rating
def customRecommendMovieFromGenre(userId, genreName):
    print("CustomRecommendMovieFromGenre")
    counter = 0
    stop = 0
    recommendedMovies = get_recommended_movies_by_id(userId)
    genreId = getGenreId(genreName)

    filtered = movie_df[movie_df["genre"] == genreId]
    if (not filtered.empty):
        movieSuggestions = filtered.sort_values(['userRating', 'rating', 'playcount'], ascending=[False, False, False])
        availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]["movieId"].item())

        while not availableOn or getMovieName(movieSuggestions.iloc[counter]["movieId"].item()) in recommendedMovies:
            counter += 1
            if counter == len(movieSuggestions):
                stop = 1    
                break
            availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]["movieId"].item())

        if (stop == 1):
            recommendation = {}
        else: 
            recommendation = {'movieId': movieSuggestions.iloc[counter]["movieId"].item(), 'titel': movieSuggestions.iloc[counter]['name'], 'platforms': availableOn}
            update_recommended_movies_by_id(userId, recommendation['titel'])

    else: 
        print("no film in db")
        recommendation = {}

    return recommendation


def customRecommendMovieFromMovie(userId, movie_name):
    counter = 0
    stop = 0
    recommendedMovies = get_recommended_movies_by_id(userId)

    movieSuggestions = pd.DataFrame(columns=['movieId','name', 'rating', 'userRating', 'playcount'])

    for index, row in user_df.iterrows():
        if(userId != row["userId"] and row["recommendedMovies"].count(movie_name)>0):
            for movie in row["recommendedMovies"]:
                movie_filter = movie_df[movie_df["name"] == movie]
                if(not movie_filter.empty and movie_filter["name"].item() != movie_name):
                    movieSuggestions = movieSuggestions.append({'movieId': movie_filter["movieId"].item(), 'name': movie_filter["name"].item(), 'rating': movie_filter["rating"].item(), 'userRating': movie_filter["userRating"].item(), 'playcount': movie_filter["playcount"].item()}, ignore_index=True)
                    
    movieSuggestions = movieSuggestions.sort_values(['userRating', 'rating', 'playcount'], ascending=[False, False, False])
    
    if(not movieSuggestions.empty):
        availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]['movieId'])

        while not availableOn or getMovieName(movieSuggestions.iloc[counter]['movieId']) in recommendedMovies:
            counter += 1

            if counter == len(movieSuggestions):
                stop = 1
                break
            availableOn = comparePlatforms(userId, movieSuggestions.iloc[counter]["movieId"])

        if (stop == 1):
            recommendation = {}
        else: 
            recommendation = { 'movieId': movieSuggestions.iloc[counter]["movieId"], 'titel': movieSuggestions.iloc[counter]['name'], 'platforms': availableOn}
            update_recommended_movies_by_id(userId, recommendation['titel'])
    else:
        recommendation = {}


    print(recommendation)
    return recommendation

#end insert

# returns an object with movie name, id and available plattforms
# or an empty object if nohting matching is possible
def recommendMovieFromGenre(userId, genreName):
    print("recommendMovieFromGenre")
    counter = 0
    pageNumber = 1
    dislikedGenre = get_disliked_genre_by_id(userId)
    movieSuggestions = getMovieIdsFromGenre(genreName, pageNumber, dislikedGenre)
    recommendedMovies = get_recommended_movies_by_id(userId)
    availableOn = comparePlatforms(userId, movieSuggestions[counter])

    ## increase counter as movie has already been recommended or is not available to the user
    while not availableOn or getMovieName(movieSuggestions[counter]) in recommendedMovies:
        counter += 1
        if counter == len(movieSuggestions):
            counter = 0
            pageNumber += 1
            movieSuggestions = getMovieIdsFromGenre(genreName, pageNumber, dislikedGenre)
        if not movieSuggestions:
            break
        availableOn = comparePlatforms(userId, movieSuggestions[counter])
    
    if not movieSuggestions:
        recommendation = {}
    else: 
        movieSuggestionName = getMovieName(movieSuggestions[counter])
        recommendation = { 'movieId': movieSuggestions[counter], 'titel': movieSuggestionName, 'platforms': availableOn}
        update_recommended_movies_by_id(userId, recommendation['titel'])
        #update_last_watched_movie_by_id(userId, recommendation['titel'], True)
    print(recommendation)
    return recommendation

# returns an object with movie name, id and available plattforms
# or an empty object if nohting matching is possible
def recommendMovieFromActress(userId, actressName):
    print("recommendMovieFromActress")
    counter = 0
    pageNumber = 1
    dislikedGenre = get_disliked_genre_by_id(userId)
    actressId = getActressId(actressName)
    if actressId == 0:
        recommendation = {}
    else:
        movieSuggestions = getMovieIdsFromActressId(actressId, pageNumber, dislikedGenre)
        print("movieSuggestions")
        print(movieSuggestions)
        recommendedMovies = get_recommended_movies_by_id(userId)
        print("recommendedMovies %s"%(recommendedMovies))
        availableOn = comparePlatforms(userId, movieSuggestions[counter])
        print("recommendMovieFromActress availableOn %s"%(availableOn))
        ## increase counter as movie has already been recommended or is not available to the user
        while len(availableOn) == 0 or getMovieName(movieSuggestions[counter]) in recommendedMovies:
            print("while")
            print("not avaibale: %s" %(availableOn))
            print("not avaibale Name: %s" %(getMovieName(movieSuggestions[counter])))
            counter += 1
            if counter == len(movieSuggestions):
                counter = 0
                pageNumber += 1
                movieSuggestions = getMovieIdsFromActressId(actressId, pageNumber, dislikedGenre)
            if not movieSuggestions:
                break
            availableOn = comparePlatforms(userId, movieSuggestions[counter])
            print("back to while loop: availableOn %s"%(availableOn))
        
        if not movieSuggestions:
            print("no movie suggestions")
            recommendation = {}
        else:
            print("should work")
            movieSuggestionName = getMovieName(movieSuggestions[counter])
            recommendation = { 'movieId': movieSuggestions[counter], 'titel': movieSuggestionName, 'platforms': availableOn}
            update_recommended_movies_by_id(userId, recommendation['titel'])
            #update_last_watched_movie_by_id(userId, recommendation['titel'], True)

    print("recommendation: %s"%(recommendation))
    return recommendation


# returns an object with movie name, id and available plattforms
# or an empty object if nohting matching is possible
def recommendMovieFromMovie(userId, movieName):
    print("recommendMovieFromMovie")
    counter = 0
    pageNumber = 1
    dislikedGenre = get_disliked_genre_by_id(userId)
    movieId = getMovieID(movieName)
    if movieId == 0:
        recommendation = {}
    else:
        movieSuggestions = getMovieIdsFromMovieId(movieId)
        recommendedMovies = get_recommended_movies_by_id(userId)
        availableOn = comparePlatforms(userId, movieSuggestions[counter])
        ## increase counter as movie has already been recommended or is not available to the user
        while not availableOn or getMovieName(movieSuggestions[counter]) in recommendedMovies or Movie().details(movieSuggestions[counter]).genres[0].name in dislikedGenre:
            counter += 1
            if counter == len(movieSuggestions):
                counter = 0
                pageNumber += 1
                movieSuggestions = getMovieNamesfromMovieId(movieId)
            if not movieSuggestions:
                break
            availableOn = comparePlatforms(userId, movieSuggestions[counter])
        
        if not movieSuggestions:
            recommendation = {}
        else: 
            movieSuggestionName = getMovieName(movieSuggestions[counter])
            recommendation = { 'movieId': movieSuggestions[counter], 'titel': movieSuggestionName, 'platforms': availableOn}
            update_recommended_movies_by_id(userId, recommendation['titel'])
            # update_last_watched_movie_by_id(userId, recommendation['titel'], True)

    print(recommendation)
    return recommendation

## Add the recommendation to our database or increase playcount
def acceptRecommendation(userId):
    print("acceptedRecommendation")
    recommendedMovies = (get_recommended_movies_by_id(userId))
    lastRecommendedMovieName = recommendedMovies[-1]
    update_last_watched_movie_by_id(userId, lastRecommendedMovieName)
    movieId = getMovieID(lastRecommendedMovieName)
    clear_recommended_again_by_id(userId)
    if check_movie_exists_by_id(movieId):
        print("increase")
        increase_playcount(movieId)
    else:
        print("add")
        movie = getMovieMeta(movieId)
        add_movie(movie)


## returns the platforms the movie is available on which the users uses as array of strings
def comparePlatforms(userId, movieId):
    print("comparePlatforms")
    language = get_language_by_id(userId)
    userPlatforms = get_streaming_platforms_by_id(userId)
    moviePlatforms = getMoviePlatforms(movieId, [language]) #among the platforms the given movie is available on, this gets the ones that the user has saved in his profile (grouped by country).
    #moviePlatforms = {'DE':{'rent':["Amazon Video"],'buy':["Amazon Video"],'flatrate':["Amazon Prime Video"]}}
    availableOn = []
    #availableOn = ["Amazon Prime Video"] ###debug
    print("availableOn %s"%(availableOn))
    for userPlatform in userPlatforms:
        print("userPlatform %s"%(userPlatform))
        for country in moviePlatforms:
            if country == language:
                print("country %s"%(country))
                try:
                    for platform in moviePlatforms[language]['buy']:
                        print("platform buy %s"%(platform))
                        if platform == userPlatform and platform not in availableOn:
                            availableOn.append(platform)
                            print("availableOn buy %s"%(availableOn))
                except KeyError:
                    print("KeyError buy")
                    pass
                try:
                    for platform in moviePlatforms[language]['rent']:
                        print("platform rent %s"%(platform))
                        if platform == userPlatform and platform not in availableOn:
                            availableOn.append(platform)
                            print("availableOn rent%s"%(availableOn))
                except KeyError:
                    print("KeyError rent")
                    pass
                try:
                    for platform in moviePlatforms[language]['flatrate']:
                        print("platform flatrate %s"%(platform))
                        if platform == userPlatform and platform not in availableOn:
                            availableOn.append(platform)
                            print("availableOn flatrate %s"%(availableOn))
                except KeyError:
                    print("KeyError flatrate")
                    pass
    print("availableOn %s"%(availableOn))
    return availableOn

## returns a recommendation as a sentence
def recommendationSentenceFromActress(userId):
    print("recommendationSentenceFromActress")
    favouriteActress = get_favourite_actress_by_id(userId)
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromActress(userId, favouriteActress)
    else:
        recommendation = customRecommendMovieFromActress(userId, favouriteActress)
        if(not recommendation):
            recommendation = recommendMovieFromActress(userId, favouriteActress)

    recommendationResult = {'success': False, 'sentence': ""}
    if recommendation:
        smallCast = getMovieCastSmall(recommendation['movieId'])
        platforms = recommendation['platforms'][0]
        for platform in recommendation['platforms']:
            if platform != recommendation['platforms'][0]:
                platforms = platforms + " and " + platform

        recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns a recommendation as a sentence
def recommendationSentenceFromGenre(userId):
    print("recommendationSentenceFromGenre")
    favouriteGenre = get_liked_genre_by_id(userId)
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromGenre(userId, favouriteGenre)
    else:
        recommendation = customRecommendMovieFromGenre(userId, favouriteGenre)
        if(not recommendation):
            recommendation  = recommendMovieFromGenre(userId, favouriteGenre)
        
    smallCast = getMovieCastSmall(recommendation['movieId'])
    platforms = recommendation['platforms'][0]
    for platform in recommendation['platforms']:
        if platform != recommendation['platforms'][0]:
            platforms = platforms + " and " + platform

    recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns a recommendation as a sentence
def recommendationSentenceFromMovie(userId):
    print("recommendationSentenceFromMovie")
    favouriteMovie = get_favourite_movie_by_id(userId)
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromMovie(userId, favouriteMovie)
    else:
        recommendation = customRecommendMovieFromMovie(userId, favouriteMovie)
        if(not recommendation):
            recommendation = recommendMovieFromMovie(userId, favouriteMovie)
    
    recommendationResult = {'success': False, 'sentence': ""}
    if recommendation:
        smallCast = getMovieCastSmall(recommendation['movieId'])
        platforms = recommendation['platforms'][0]
        for platform in recommendation['platforms']:
            if platform != recommendation['platforms'][0]:
                platforms = platforms + " and " + platform

        recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns a recommendation as a sentence and uses intent input
def recommendationSentenceFromActressInput(userId, actressName):
    print("recommendationSentenceFromActressInput")
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromActress(userId, actressName)
    else:
        recommendation = customRecommendMovieFromActress(userId, actressName)
        if(not recommendation):
            recommendation = recommendMovieFromActress(userId, actressName)


    recommendationResult = {'success': False, 'sentence': ""}
    if recommendation:
        smallCast = getMovieCastSmall(recommendation['movieId'])
        platforms = recommendation['platforms'][0]
        for platform in recommendation['platforms']:
            if platform != recommendation['platforms'][0]:
                platforms = platforms + " and " + platform

        recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns a recommendation as a sentence and uses intent input
def recommendationSentenceFromGenreInput(userId, genreName):
    print("recommendationSentenceFromGenreInput")
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromGenre(userId, genreName)
    else:
        recommendation = customRecommendMovieFromGenre(userId, genreName)
        if(not recommendation):
            recommendation  = recommendMovieFromGenre(userId, genreName)
    
    smallCast = getMovieCastSmall(recommendation['movieId'])
    platforms = recommendation['platforms'][0]
    for platform in recommendation['platforms']:
        if platform != recommendation['platforms'][0]:
            platforms = platforms + " and " + platform

    recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns a recommendation as a sentence and uses intent input
def recommendationSentenceFromMovieInput(userId, movieName):
    print("recommendationSentenceFromMovieInput")
    
    recommendedMovies = get_recommended_movies_by_id(userId)
    amountRecommendedMovies = len(recommendedMovies)
    if(amountRecommendedMovies < 5):
        recommendation = recommendMovieFromMovie(userId, movieName)
    else:
        recommendation = customRecommendMovieFromMovie(userId, movieName)
        if(not recommendation):
            recommendation = recommendMovieFromMovie(userId, movieName)
    
    recommendationResult = {'success': False, 'sentence': ""}
    if recommendation:
        smallCast = getMovieCastSmall(recommendation['movieId'])
        platforms = recommendation['platforms'][0]
        for platform in recommendation['platforms']:
            if platform != recommendation['platforms'][0]:
                platforms = platforms + " and " + platform

        recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## general recommender which is based on user likings
def generalRecommendation(userId):
    print("generalRecommendation")
    userLikings = get_likings_by_id(userId)

    recommendationResult = {'success': False, 'sentence': ""}
    
    maxLiking = max(userLikings.items(), key=operator.itemgetter(1))[0]

    if maxLiking == "acting":
        recommendationResult = recommendationSentenceFromActress(userId)
    elif maxLiking == "movie":
        recommendationResult = recommendationSentenceFromMovie(userId)
    elif maxLiking == "genre":
        recommendationResult = recommendationSentenceFromGenre(userId)

    return recommendationResult

## recommendation from already recommended movies
def recommendAgain(userId):
    print("recommendAgain")
    recommendedMovies = get_recommended_movies_by_id(userId)
    recommendAgain = get_recommended_again_by_id(userId)
    recommendation = {}
    if recommendedMovies and recommendedMovies[0] != "":
        selector = random.randrange(len(recommendedMovies))
        counter = 0
        while recommendedMovies[selector] in recommendAgain and counter < len(recommendedMovies):
            selector = random.randrange(len(recommendedMovies))
            counter += 1
        if counter < len(recommendedMovies):
            movieSuggestionName = recommendedMovies[selector]
            movieSuggestionId = getMovieID(movieSuggestionName)
            availableOn = comparePlatforms(userId, movieSuggestionId)
            update_recommended_again_by_id(userId, movieSuggestionName)
            recommendation = { 'movieId': movieSuggestionId, 'titel': movieSuggestionName, 'platforms': availableOn}
            #update_last_watched_movie_by_id(userId, movieSuggestionName)

    print(recommendation)
    return recommendation

## returns a recommendation as a sentence using old recommendations
def recommendationSentenceFromAgain(userId):
    print("recommendationSentenceFromAgain")
    recommendation = recommendAgain(userId)
    recommendationResult = {'success': False, 'sentence': ""}

    if recommendation: 
        smallCast = getMovieCastSmall(recommendation['movieId'])
        platforms = recommendation['platforms'][0]
        for platform in recommendation['platforms']:
            if platform != recommendation['platforms'][0]:
                platforms = platforms + " and " + platform
        recommendationResult = {'success': True, 'sentence': "I recommend %s with %s and %s available on %s."%(recommendation['titel'], smallCast[0], smallCast[1], platforms)}
    return recommendationResult

## returns the last recommendation
def lastRecommendationSentence(userId):
    print("lastRecommendationSentence")
    lastRecommendationName = get_recommended_movies_by_id(userId)[-1]
    recommendationResult = {'success': False, 'sentence': ""}

    if lastRecommendationName:
        lastRecommendationId = getMovieID(lastRecommendationName)
        availableOn = comparePlatforms(userId, lastRecommendationId)
        smallCast = getMovieCastSmall(lastRecommendationId)
        platforms = availableOn[0]
        for platform in availableOn:
            if platform != availableOn[0]:
                platforms = platforms + " and " + platform
        recommendationResult = {'success': True, 'sentence': "The last recommendation has been %s with %s and %s available on %s."%(lastRecommendationName, smallCast[0], smallCast[1], platforms)}
    return recommendationResult
