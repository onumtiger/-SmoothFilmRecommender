from tmdbv3api import TMDb
tmdb = TMDb()
tmdb.api_key = '93a8c2d922b414294a124ef8dc9c2428'

from tmdbv3api import Movie
from tmdbv3api import Discover
from tmdbv3api import Person
from tmdbv3api import Search
from tmdbv3api import Genre

import requests

from movie_firebase_functions import newMovie

####
# getter functions
###

## return movie id as int
def getMovieID(movieName):
    print("getMovieID")
    searchResult = Movie().search(movieName)
    movieId = 0
    if searchResult[0].id > 0:
        for movie in searchResult: #try to find an exact match first
            if getMovieName(movie.id).lower() == movieName.lower(): #case-insensitive matching
                movieId = movie.id
                break
        if movieId is 0: #if no exact matching can be found, try the top search result
            movieId = searchResult[0].id
    print("movieId: %i"%(movieId))
    return movieId

## returns movie name as String
def getMovieName(movieId):
    print("getMovieName")
    if movieId is 0 or not Movie().details(movieId).title:
        return ""
    return Movie().details(movieId).title

## get movie metda data as array
def getMovieMeta(movieId):
    if type(movieId) != int:
        movieId = getMovieID(movieId)
    movieTitle = Movie().details(movieId).original_title
    print("movieTitle: %s"%(movieTitle))
    movieAdult = Movie().details(movieId).adult
    print("movieAdult: %s"%(movieAdult))
    movieRating = Movie().details(movieId).vote_average
    print("movieRating: %f"%(movieRating))
    movieGenre = Movie().details(movieId).genres[0].id
    print("movieGenre: %i"%(movieGenre))
    movieLanguages = getMovieTranslations(movieId)
    print("movieLanguages: %s"%(movieLanguages))
    movieCast = getMovieCast(movieId)
    print("movieCast: %s"%(movieCast))
    # movieKeywords = Movie().details(movieId).keywords.keywords[0].id
    moviePlatforms = getMoviePlatforms(movieId, movieLanguages)

    movie = newMovie(movieId, movieTitle, movieCast, movieGenre, moviePlatforms, movieLanguages, movieRating, movieAdult)
    # movie = newMovie(movieId, movieTitle, movieCast, movieGenre, movieKeywords, moviePlatforms, movieLanguages, movieRating, movieAdult)
    return movie

## returns cast as an array of Ids int
def getMovieCast(movieId):
    print("getMovieCast")
    if type(movieId) != int:
        movieId = getMovieID(movieId)
    searchResult = Movie().credits(movieId).cast
    cast = []
    for actress in searchResult:
        cast.append(actress.id)
    print("cast %s"%(cast))
    return cast

## returns the two first actresses from a movie as a Name
def getMovieCastSmall(movieId):
    print("getMovieCastSmall")
    cast = getMovieCast(movieId)
    if not cast:
        return []
    else: 
        print("smallcast %s"%([getActressName(cast[0]), getActressName(cast[1])]))
        return [getActressName(cast[0]), getActressName(cast[1])]
    
## returns array of strings (z.b. ['en', 'es'])
def getMovieTranslations(movieId):
    print("getMovieTranslations")
    searchResult = Movie().details(movieId).translations.translations
    translations = []
    for language in searchResult:
        translations.append(language.iso_639_1)
    print("translations %s"%(translations))
    return translations

## returns dictionary of languages with platforms to rent, buy and flatrate, filtered by a languages array of languages of interest
## e.g. {'US': {'buy': ["netflix"], 'rent': ["netflix"]}}
def getMoviePlatforms(movieId, languages):
    print("getMoviePlatforms")
    languages = transformToUpper(languages)
    if type(movieId) != int:
        movieId = getMovieID(movieId)
    print("movie id %i"%(movieId))
    searchResult = requests.get('https://api.themoviedb.org/3/movie/%s/watch/providers?api_key=%s'%(movieId, tmdb.api_key)).json()['results']
    # print("searchResult %s"%(searchResult))
    platforms = {}
    for language in searchResult:
        buy = []
        rent = []
        flatrate = []
        if language in languages:
            if 'buy' in searchResult['%s'%(language)]:
                for provider in searchResult['%s'%(language)]['buy']:
                    buy.append(provider['provider_name'])
                print("buy %s"%(buy))
            if 'rent' in searchResult['%s'%(language)]:
                for provider in searchResult['%s'%(language)]['rent']:
                    rent.append(provider['provider_name'])
                print("rent %s"%(rent))
            if 'flatrate' in searchResult['%s'%(language)]:
                for provider in searchResult['%s'%(language)]['flatrate']:
                    flatrate.append(provider['provider_name'])
                print("flatrate %s"%(flatrate))
            platforms['%s'%(language)] = {'buy': buy, 'rent': rent, 'flatrate': flatrate}
    print("platforms %s"%(platforms))
    return platforms

## transform array to uppercase
def transformToUpper(array):
    print("transformToUpper")
    upperArray = []
    for element in array:
        upperArray.append(element.upper())
    print("upperArray %s"%(upperArray))
    return upperArray

## return actress id as int 
def getActressId(actressName):
    print("getActressID")
    searchResult = Person().search(actressName)
    if not searchResult:
        print("Actress Id %i"%(0))
        return 0
    else:
        print("Actress Id %i"%(searchResult[0].id))
        return searchResult[0].id

## return actress name as String
def getActressName(actressId):
    print("getActressName")
    if actressId > 0 :
        print("Actress Name %s"%(Person().details(actressId).name))
        return Person().details(actressId).name
    else:
        print("Actress Name %s"%(""))
        return ""

## returns 20 movie titles as an array of strings
def getMoviesFromActressId(actressId, pageNumber, dislikedGenreName):
    print("getMoviesFromActressId")
    dislikedGenreId = getGenreId(dislikedGenreName)
    searchResult = Discover().discover_movies({
            'with_cast': actressId,
            'without_genres': dislikedGenreId,
            'sort_by': 'popularity.desc',
            'page': pageNumber
    })
    movieList = []
    for movie in searchResult:
        movieList.append(movie.title)
    print("movieList %s"%(movieList))
    return movieList

## returns 20 movie titles as an array of int
def getMovieIdsFromActressId(actressId, pageNumber, dislikedGenreName):
    print("getMoviesFromActressId")
    dislikedGenreId = getGenreId(dislikedGenreName)
    searchResult = Discover().discover_movies({
            'with_cast': actressId,
            'without_genres': dislikedGenreId, 
            'sort_by': 'popularity.desc',
            'page': pageNumber
    })
    movieList = []
    for movie in searchResult:
        movieList.append(movie.id)
    print("movieList %s"%(movieList))
    return movieList

## returns 20 movie titles as an array
def getMoviesFromGenre(genreName, pageNumber, dislikedGenreName):
    print("getMoviesFromGenre")
    genreId = getGenreId(genreName)
    dislikedGenreId = getGenreId(dislikedGenreName)
    searchResult = Discover().discover_movies({
            'with_genres' : genreId,
            'without_genres': dislikedGenreId, 
            'sort_by': 'popularity.desc',
            'page': pageNumber
    })
    movieList = []
    for movie in searchResult:
        movieList.append(movie.title)
    print("movieList %s"%(movieList))
    return movieList

## returns 20 movie titles as an array
def getMovieIdsFromGenre(genreName, pageNumber, dislikedGenreName):
    print("getMovieIdsFromGenre")
    genreId = getGenreId(genreName)
    dislikedGenreId = getGenreId(dislikedGenreName)
    searchResult = Discover().discover_movies({
            'with_genres': genreId,
            'without_genres': dislikedGenreId, 
            'sort_by': 'popularity.desc',
            'page': pageNumber
    })
    movieList = []
    for movie in searchResult:
        movieList.append(movie.id)
    print("movieList %s"%(movieList))
    return movieList

## returns 20 movie titles as an array
def getMovieIdsFromMovieId(movieId):
    print("getMovieIdsFromMovieId")
    searchResult = Movie().similar(movieId)
    movieList = []
    for movie in searchResult:
        movieList.append(movie.id)
    print("movieList %s"%(movieList))
    return movieList

## returns 20 movie titles as an array
def getMovieNamesfromMovieId(movieId):
    print("getMovieIdsFromMovieId")
    searchResult = Movie().similar(movieId)
    movieList = []
    for movie in searchResult:
        movieList.append(movie.title)
    print("movieList %s"%(movieList))
    return movieList

## returns gerneID as int
def getGenreId(genreName):
    print("getGenreId")
    genreId = 0
    genres = Genre().movie_list()
    for g in genres:
        if g.name == genreName:
            genreId = g.id
    return genreId

## retuns gerneName as String
def getGenreName(genreId):
    print("getGenreName")
    genreName = ""
    genres = Genre().movie_list()
    for g in genres:
        if g.id == genreId:
            genreName = g.name
    print("genreName %s"%(genreName))
    return genreName

### genre list
# 28
# Action
# 12
# Adventure
# 16
# Animation
# 35
# Comedy
# 80
# Crime
# 99
# Documentary
# 18
# Drama
# 10751
# Family
# 14
# Fantasy
# 36
# History
# 27
# Horror
# 10402
# Music
# 9648
# Mystery
# 10749
# Romance
# 878
# Science Fiction
# 10770
# TV Movie
# 53
# Thriller
# 10752
# War
# 37
# Western

## platform list
# "Netflix", 
# "Amazon Prime Video", 
# "Amazon Video", 
# "Disney Plus", 
# "Apple iTunes",
# "Google Play Movies",
# "Microsoft Store"
# "Sky Store"