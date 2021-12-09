# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.intent import Intent
from ask_sdk_model.dialog import (ElicitSlotDirective, DelegateDirective)
from ask_sdk_model.dialog_state import DialogState
from ask_sdk_model.slu.entityresolution.status_code import StatusCode

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

### api ###
import tmdbv3api
from tmdbv3api import TMDb

from tmdbv3api import Movie
from tmdbv3api import Discover
from tmdbv3api import Person
from tmdbv3api import Search
from tmdbv3api import Genre

tmdb = TMDb()
tmdb.api_key = '93a8c2d922b414294a124ef8dc9c2428'

### firebase ###
import firebase_admin 
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred)

firestore_db = firestore.client()

### canonical slot value constants ###
FEEDBACK_POSITIVE = 'good'
FEEDBACK_NEGATIVE = 'bad'

RECOMMENDATION_ACCEPTED = "Okay"
RECOMMENDATION_REJECTED = "Something else"

### response templates ###
SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION = "I'm happy to take a new recommendation request, but please give me feedback on my last recommendation first, which was the film {}. "
SENTENCE_NO_RECOMMENDATION_FOUND = "I'm sorry. I was not able to find a {} recommendation available on your platforms based on your input. "
SENTENCE_MOVIE_NOT_FOUND = "Hmm, I don't know the film {}. "
SENTENCE_ACTOR_NOT_FOUND = "Sorry, I don't know the actor or actress {}. "
SENTENCE_GENRE_NOT_FOUND = "Hmm, I don't recognize {} as a genre. "
SENTENCE_DID_NOT_UNDERSTAND = "Sorry, I didn't get that. "
SENTENCE_RECOMMENDATION_ACCEPTED = "Great! Enjoy the film! "
SENTENCE_ANOTHER_RECOMMENDATION =  "Okay. "
SENTENCE_CANCELED = "Okay, maybe another time. "
SENTENCE_FEEDBACK_ACCEPTED = "Alright, I will try to work your feedback into my next recommendations. "
SENTENCE_BACK_TO_RECOMMENDATION = "Back to your recommendation request... "
SENTENCE_FEEDBACK_WAS_POSITIVE = "Great to hear! "
SENTENCE_FEEDBACK_WAS_NEGATIVE = "I'm sorry to hear that. "

PROMPT_TRY_AGAIN = "Why don't you try again with a different request? If you need help, just say: Help. "
PROMPT_MOVIE_NOT_FOUND = "Please tell me the movie's official English title. "
PROMPT_ACTOR_NOT_FOUND = "Please use their commonly known name. "
PROMPT_GENRE_NOT_FOUND = "Try a more common synonym or a more widely known genre. "
PROMPT_RECOMMENDATION_CONFIRMATION = "You can say Okay to accept this recommendation or request another one by saying: Another one. To cancel, just say Stop. "
PROMPT_ANOTHER_RECOMMENDATION = "How about this one? "
PROMPT_FEEDBACK_ASPECTS = "What specifically {} you like about {}? That could be the acting, the story, or the setting of the movie. "

### other templates ###
DELDIR_FEEDBACK = DelegateDirective(Intent(
    name="feedbackIntent",
    slots={
        "feedbackGeneral": {
            "name": "feedbackGeneral"
        },
        "feedbackAspects": {
            "name": "feedbackAspects"
        }
    }
))

def makeESDir(slotname, intent=None):
    if intent:
        return (ElicitSlotDirective(
                slot_to_elicit = slotname,
                updated_intent = intent
            ))
    else:
        return (ElicitSlotDirective(
                slot_to_elicit = slotname
            ))


### own functions ###
from sentimentAnalysis import *
from recommender_functions import *
from user_firebase_functions import *
from movie_api_functions import *

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        responseBuilder = handler_input.response_builder
        userID = str(handler_input.request_envelope.context.system.user.user_id)
        speak_output = "Welcome to Movie Tips! "
        
        if check_user_exists_by_id(userID):
            speak_output = "Welcome back {}! ".format(get_username_by_id(userID))
            if is_last_watched_movie_rated_by_id(userID):
                speak_output += "Do you want me to recommend a movie? If so, just say: Recommend something."
                responseBuilder.speak(speak_output).ask(speak_output)
            else:
                speak_output += "I see you haven't rated my last recommendation yet, which was the film {}. Let's do that now! ".format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
        else:
            speak_output += "I see you haven't set up a profile yet. Let's do that now! "
            responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                    name="setupIntent" #weirdly enough, we don't have to pass the slots here and it works anyway... as opposed to the feedbackIntent which has Alexa completely checking out after the first prompt unless the slots are given. What even is this madness
                )))
        
        return responseBuilder.response



class RecommendationByMovieIntentHandler(AbstractRequestHandler):
    """Handler for Recommendation by Movie Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("recommendationIntent_byMovie")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        userID = handler_input.request_envelope.context.system.user.user_id
        slot_movie = intent.slots["movieTitle"]
        slot_confirmation = intent.slots["recommendationOK"]
        
        if request.dialog_state == DialogState.STARTED or slot_movie.value is None:
            if is_last_watched_movie_rated_by_id(userID):
                
                #resolve "my favorite movie" if necessary
                resolution = slot_movie.resolutions.resolutions_per_authority[0]
                if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                    resolvedSlotID = resolution.values[0].value.id
                    if resolvedSlotID == "FAV":
                        slot_movie.value = get_favourite_movie_by_id(userID)
                
                movieID = getMovieID(slot_movie.value)
                movieName = getMovieName(movieID)
                
                if movieID == 0:
                    speak_output = SENTENCE_MOVIE_NOT_FOUND.format(slot_movie.value)
                    prompt_output = PROMPT_MOVIE_NOT_FOUND
                    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("movieTitle"))
                else:
                    slot_movie.value = movieName
                    
                    rec = recommendationSentenceFromMovieInput(userID, movieName)
                    if rec['success']:
                        speak_output = rec['sentence']
                        responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                
            else:
                speak_output = SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION.format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
            
        
        elif request.dialog_state == DialogState.IN_PROGRESS: #confirmation given for recommendation
            resolution = slot_confirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_confirmation.value = inputVal
                if inputVal == RECOMMENDATION_ACCEPTED:
                    responseBuilder.add_directive(DelegateDirective(intent))
                elif inputVal == RECOMMENDATION_REJECTED:
                    rec = recommendationSentenceFromMovieInput(userID, slot_movie.value)
                    if rec['success']:
                        speak_output = SENTENCE_ANOTHER_RECOMMENDATION
                        prompt_output = PROMPT_ANOTHER_RECOMMENDATION+rec['sentence']+" "+PROMPT_RECOMMENDATION_CONFIRMATION
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else: #We're told to cancel/stop
                    speak_output = SENTENCE_CANCELED
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                        name="AMAZON.CancelIntent"
                    )))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_RECOMMENDATION_CONFIRMATION
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
            
        else: #request.dialog_state == DialogState.COMPLETED; we have a green light on the recommendation at this point
            acceptRecommendation(userID)
            speak_output = SENTENCE_RECOMMENDATION_ACCEPTED
            responseBuilder.speak(speak_output)
        
        return responseBuilder.response


class RecommendationByActorIntentHandler(AbstractRequestHandler):
    """Handler for Recommendation by Actor Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("recommendationIntent_byActor")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        userID = handler_input.request_envelope.context.system.user.user_id
        slot_actor = intent.slots["actor"]
        slot_confirmation = intent.slots["recommendationOK"]
        
        if request.dialog_state == DialogState.STARTED or slot_actor.value is None:
            if is_last_watched_movie_rated_by_id(userID):
                
                #resolve "my favorite actor" if necessary
                resolution = slot_actor.resolutions.resolutions_per_authority[0]
                if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                    resolvedSlotID = resolution.values[0].value.id
                    if resolvedSlotID == "FAV":
                        slot_actor.value = get_favourite_actress_by_id(userID)
                
                actorID = getActressId(slot_actor.value)
                actorName = getActressName(actorID)
                
                if actorID == 0:
                    speak_output = SENTENCE_ACTOR_NOT_FOUND.format(slot_actor.value)
                    prompt_output = PROMPT_ACTOR_NOT_FOUND
                    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("actor"))
                else:
                    slot_actor.value = actorName

                    rec = recommendationSentenceFromActressInput(userID, actorName)
                    if rec['success']:
                        speak_output = rec['sentence']
                        responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                
            else:
                speak_output = SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION.format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
            
        
        elif request.dialog_state == DialogState.IN_PROGRESS: #confirmation given for recommendation
            resolution = slot_confirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_confirmation.value = inputVal
                if inputVal == RECOMMENDATION_ACCEPTED:
                    responseBuilder.add_directive(DelegateDirective(intent))
                elif inputVal == RECOMMENDATION_REJECTED:
                    rec = recommendationSentenceFromActressInput(userID, slot_actor.value)
                    if rec['success']:
                        speak_output = SENTENCE_ANOTHER_RECOMMENDATION
                        prompt_output = PROMPT_ANOTHER_RECOMMENDATION+rec['sentence']+" "+PROMPT_RECOMMENDATION_CONFIRMATION
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else: #We're told to cancel/stop
                    speak_output = SENTENCE_CANCELED
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                        name="AMAZON.CancelIntent"
                    )))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_RECOMMENDATION_CONFIRMATION
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
            
        else: #request.dialog_state == DialogState.COMPLETED; we have a green light on the recommendation at this point
            acceptRecommendation(userID)
            speak_output = SENTENCE_RECOMMENDATION_ACCEPTED
            responseBuilder.speak(speak_output)
        
        return responseBuilder.response


class RecommendationByGenreIntentHandler(AbstractRequestHandler):
    """Handler for Recommendation by Genre Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("recommendationIntent_byGenre")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        userID = handler_input.request_envelope.context.system.user.user_id
        slot_genre = intent.slots["genre"]
        slot_confirmation = intent.slots["recommendationOK"]
        
        if request.dialog_state == DialogState.STARTED or slot_genre.value is None:
            if is_last_watched_movie_rated_by_id(userID):
                
                #resolve "my favorite genre" if necessary
                resolution = slot_genre.resolutions.resolutions_per_authority[0]
                if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                    resolvedSlotID = resolution.values[0].value.id
                    resolvedSlotName = resolution.values[0].value.name
                    if resolvedSlotID == "FAV":
                        slot_genre.value = get_liked_genre_by_id(userID)
                    else:
                        slot_genre.value = resolvedSlotName
                    
                    rec = recommendationSentenceFromGenreInput(userID, slot_genre.value)
                    if rec['success']:
                        speak_output = rec['sentence']
                        responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else:
                    speak_output = SENTENCE_GENRE_NOT_FOUND.format(slot_genre.value)
                    prompt_output = PROMPT_GENRE_NOT_FOUND
                    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("genre"))
                
            else:
                speak_output = SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION.format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
            
        
        elif request.dialog_state == DialogState.IN_PROGRESS: #confirmation given for recommendation
            resolution = slot_confirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_confirmation.value = inputVal
                if inputVal == RECOMMENDATION_ACCEPTED:
                    responseBuilder.add_directive(DelegateDirective(intent))
                elif inputVal == RECOMMENDATION_REJECTED:
                    rec = recommendationSentenceFromGenreInput(userID, slot_genre.value)
                    if rec['success']:
                        speak_output = SENTENCE_ANOTHER_RECOMMENDATION
                        prompt_output = PROMPT_ANOTHER_RECOMMENDATION+rec['sentence']+" "+PROMPT_RECOMMENDATION_CONFIRMATION
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else: #We're told to cancel/stop
                    speak_output = SENTENCE_CANCELED
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                        name="AMAZON.CancelIntent"
                    )))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_RECOMMENDATION_CONFIRMATION
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
            
        else: #request.dialog_state == DialogState.COMPLETED; we have a green light on the recommendation at this point
            acceptRecommendation(userID)
            speak_output = SENTENCE_RECOMMENDATION_ACCEPTED
            responseBuilder.speak(speak_output)
        
        return responseBuilder.response



class RecommendationRewatchIntentHandler(AbstractRequestHandler):
    """Handler for Recommendation Rewatch Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("recommendationIntent_rewatch")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        userID = handler_input.request_envelope.context.system.user.user_id
        slot_confirmation = intent.slots["recommendationOK"]
        
        if request.dialog_state == DialogState.STARTED: #"recommend a rewatch"/...
            if is_last_watched_movie_rated_by_id(userID):
                prevRecommendations = get_recommended_movies_by_id(userID)
                if prevRecommendations and len(prevRecommendations[0]): #check if we have recommendations at all
                    rec = recommendationSentenceFromAgain(userID)
                    if rec['success']:
                        speak_output = rec['sentence']
                        responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("rewatch")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                else:
                    speak_output = "Sorry, I don't have any previously accepted recommendations for you in my database that I could recommend again. Try using this feature again once you have accepted some new recommendations of mine. "
                    prompt_output = "In the meantime... "+PROMPT_TRY_AGAIN
                    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                
            else:
                speak_output = SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION.format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
            
        elif request.dialog_state == DialogState.IN_PROGRESS: #confirmation given for recommendation
            resolution = slot_confirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_confirmation.value = inputVal
                if inputVal == RECOMMENDATION_ACCEPTED:
                    responseBuilder.add_directive(DelegateDirective(intent))
                elif inputVal == RECOMMENDATION_REJECTED:
                    rec = recommendationSentenceFromAgain(userID)
                    if rec['success']:
                        speak_output = SENTENCE_ANOTHER_RECOMMENDATION
                        prompt_output = PROMPT_ANOTHER_RECOMMENDATION+rec['sentence']+" "+PROMPT_RECOMMENDATION_CONFIRMATION
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new rewatch")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else: #We're told to cancel/stop
                    speak_output = SENTENCE_CANCELED
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                        name="AMAZON.CancelIntent"
                    )))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_RECOMMENDATION_CONFIRMATION
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
            
        else: #request.dialog_state == DialogState.COMPLETED; we have a green light on the recommendation at this point
            acceptRecommendation(userID)
            speak_output = SENTENCE_RECOMMENDATION_ACCEPTED
            responseBuilder.speak(speak_output)
            
            
        return responseBuilder.response

class RecommendationIntentHandler(AbstractRequestHandler):
    """Handler for Recommendation Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("recommendationIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        userID = handler_input.request_envelope.context.system.user.user_id
        slot_confirmation = intent.slots["recommendationOK"]
        
        if request.dialog_state == DialogState.STARTED: #"i want to watch something"/...
            if is_last_watched_movie_rated_by_id(userID):
                #####
                rec = generalRecommendation(userID)
                if rec['success']:
                    speak_output = rec['sentence']
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                else:
                    speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                    prompt_output = PROMPT_TRY_AGAIN
                    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                
            else:
                speak_output = SENTENCE_FEEDBACK_BEFORE_RECOMMENDATION.format(get_last_watched_movie_by_id(userID))
                responseBuilder.speak(speak_output).add_directive(DELDIR_FEEDBACK)
            
        elif request.dialog_state == DialogState.IN_PROGRESS: #confirmation given for recommendation
            resolution = slot_confirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_confirmation.value = inputVal
                if inputVal == RECOMMENDATION_ACCEPTED:
                    responseBuilder.add_directive(DelegateDirective(intent))
                elif inputVal == RECOMMENDATION_REJECTED:
                    rec = generalRecommendation(userID)
                    if rec['success']:
                        speak_output = SENTENCE_ANOTHER_RECOMMENDATION
                        prompt_output = PROMPT_ANOTHER_RECOMMENDATION+rec['sentence']+" "+PROMPT_RECOMMENDATION_CONFIRMATION
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
                    else:
                        speak_output = SENTENCE_NO_RECOMMENDATION_FOUND.format("new")
                        prompt_output = PROMPT_TRY_AGAIN
                        responseBuilder.speak(speak_output+prompt_output).ask(prompt_output)
                    
                else: #We're told to cancel/stop
                    speak_output = SENTENCE_CANCELED
                    responseBuilder.speak(speak_output).add_directive(DelegateDirective(Intent(
                        name="AMAZON.CancelIntent"
                    )))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_RECOMMENDATION_CONFIRMATION
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("recommendationOK"))
            
        else: #request.dialog_state == DialogState.COMPLETED; we have a green light on the recommendation at this point
            acceptRecommendation(userID)
            speak_output = SENTENCE_RECOMMENDATION_ACCEPTED
            responseBuilder.speak(speak_output)
            
            
        return responseBuilder.response


class SetupIntentHandler(AbstractRequestHandler):
    """Handler for Setup Profile Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("setupIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        #at least for now, we only consider streaming options in Germany and ignore the language version of the films on a given streamer
        
        slot_name = intent.slots["name"]
        slot_streamer = intent.slots["streamer"]
        slot_favMovie = intent.slots["favMovie"]
        slot_favActor = intent.slots["favActor"]
        slot_favGenre = intent.slots["favGenre"]
        slot_dislikedGenre = intent.slots["dislikedGenre"]
        slot_finalConfirmation = intent.slots["finalConfirmation"]
        
        #check where we are in the dialog:
        # 0 = no info given yet, need to get the name first
        # 1 = name is given and to be processed, nothing else yet. Get the streamers.
        # 2 = name (processed) and streamers (to be processed) are given, get the fav movie
        # 3 = name, streamers (processed) and fav movie (to be processed) are given, get the fav actors
        # 4 = name, streamers, fav movie (processed) and fav actors (to be processed) are given, get the liked genres
        # 5 = name, streamers, fav movie, fav actors (processed) and liked genres (to be processed) are given, get the disliked genres
        # 6 = name, streamers, fav movie, fav actors, liked genres (processed) and disliked genres (to be processed) are given, process the disliked genres
        # 7 = we have all we need, so we can give some confirmation and move on.
        
        setupPhase = 0
        if request.dialog_state == DialogState.STARTED:
            if slot_name.value is None:
                setupPhase = 0
            else:
                setupPhase = 1
        elif request.dialog_state == DialogState.IN_PROGRESS:
            if slot_streamer.value is None and slot_streamer.slot_value is None:
                setupPhase = 1
            elif slot_favMovie.value is None:
                setupPhase = 2
            elif slot_favActor.value is None:
                setupPhase = 3
            elif slot_favGenre.value is None:
                setupPhase = 4
            elif slot_dislikedGenre.value is None:
                setupPhase = 5
            elif slot_finalConfirmation.value is None:
                setupPhase = 6
            else:
                setupPhase = 7
        else: #request.dialog_state == DialogState.COMPLETED
            setupPhase = 8
        
        #respond per phase:
        if setupPhase == 0:
            responseBuilder.add_directive(DelegateDirective())
            
        elif setupPhase == 1:
            inputVal = slot_name.value
            speak_output = "Hi {}! ".format(inputVal)
            responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            
        elif setupPhase == 2:
            #try to resolve slot input
            allInputs = []
            resolvedInputs = []
            if "resolvedStreamers" in sessionAttribs and sessionAttribs["resolvedStreamers"] is not None:
                resolvedInputs = list(sessionAttribs["resolvedStreamers"])
                sessionAttribs["resolvedStreamers"] = None
            currentUnresolved = {}
            
            if slot_streamer.slot_value.object_type == "List":
                for v in slot_streamer.slot_value.values:
                    allInputs.append(v)
            else:
                allInputs.append(slot_streamer.slot_value)
            
            for i in allInputs:
                resolution = i.resolutions.resolutions_per_authority[0]
                if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                    resolvedSlotName = resolution.values[0].value.name
                    resolvedSlotID = resolution.values[0].value.id
                    if resolvedSlotID in ("ATV-X", "AMZ-X", "SKY-X"):
                        currentUnresolved = {"id": resolvedSlotID, "value": i.value}
                        break
                    else:
                        resolvedInputs.append(resolvedSlotName)
                else:# if i.value not in ("the", "and", "also"): #don't ask for stuff that we don't need but Alexa can't (always) filter out by itself
                    currentUnresolved = {"id": "", "value": i.value}
                    break
            
            stringifiedResolved = resolvedInputs and ((", ".join(resolvedInputs[:-1])+" and "+resolvedInputs[-1], resolvedInputs[0])[len(resolvedInputs) == 1])
            
            if currentUnresolved:
                #response part 1
                if resolvedInputs:
                    speak_output = "I understood {}. But ".format(stringifiedResolved)
                else:
                    speak_output = "Sorry, "
                    
                #response part 2
                if currentUnresolved["id"] == "ATV-X":
                    speak_output += "I'm not sure about "+currentUnresolved["value"]+". "
                    prompt_output = "Do you mean Apple TV Plus or Apple iTunes, also known as Apple TV? "
                elif currentUnresolved["id"] == "AMZ-X":
                    speak_output += "I'm not sure about "+currentUnresolved["value"]+". "
                    prompt_output = "Do you mean Amazon Prime Video or Amazon Video? " #Alexa cuts "Amazon" as the first word out of slot inputs, because why the hell not. Should be avoidable e.g. if we preface it with one of the defined carrier phrases like "I have ...". To be safe we defined synonyms for the option without the leading "Amazon".
                elif currentUnresolved["id"] == "SKY-X":
                    speak_output += "I'm not sure about "+currentUnresolved["value"]+". "
                    prompt_output = "Do you mean Sky Ticket, Sky Go or the Sky Store? "
                else:
                    speak_output += "I don't recognize {} as a streaming service. ".format(currentUnresolved["value"])
                    prompt_output = "Please try a platform that is available in Germany. "
                
                #give the response
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("streamer"))
                #store the resolved values to pick up in the next go
                sessionAttribs["resolvedStreamers"] = resolvedInputs
            else: #implies resolvedInputs is not empty
                inputVal = stringifiedResolved
                slot_streamer.value = "|".join(resolvedInputs) ###
                speak_output = "Great! you shall only receive films available on {} as recommendations. ".format(inputVal)
                responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
                
            
            #resolution = slot_streamer.resolutions.resolutions_per_authority[0]
            #
            #if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
            #    resolvedSlotName = resolution.values[0].value.name
            #    resolvedSlotID = resolution.values[0].value.id
            #    if resolvedSlotID == "ATV-X":
            #        prompt_output = "Do you mean Apple TV Plus or Apple iTunes, also known as Apple TV? "
            #        responseBuilder.speak(prompt_output).ask(prompt_output).add_directive(esDir)
            #    elif resolvedSlotID == "AMZ-X":
            #        prompt_output = "Do you mean Amazon Prime Video or Amazon Video? " #Alexa cuts "Amazon" as the first word out of slot inputs, because why the hell not. Should be avoidable e.g. if we preface it with one of the defined carrier phrases like "I have ...". To be safe we defined synonyms for the option without the leading "Amazon".
            #        responseBuilder.speak(prompt_output).ask(prompt_output).add_directive(esDir)
            #    elif resolvedSlotID == "SKY-X":
            #        prompt_output = "Do you mean Sky Ticket, Sky Go or the Sky Store? "
            #        responseBuilder.speak(prompt_output).ask(prompt_output).add_directive(esDir)
            #    else:
            #        inputVal = resolvedSlotName
            #        slot_streamer.value = inputVal
            #        speak_output = "Great! you shall only receive films available on {} as recommendations. ".format(inputVal)
            #        responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            #else:
            #    speak_output = "Sorry, I don't recognize {} as a streaming service. ".format(slot_streamer.value)
            #    prompt_output = "Please try a platform that is available in Germany. "
            #    responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(esDir)
            
        elif setupPhase == 3:
            movieID = getMovieID(slot_favMovie.value)
            movieName = getMovieName(movieID)
            
            if movieID == 0:
                speak_output = SENTENCE_MOVIE_NOT_FOUND.format(slot_favMovie.value)
                prompt_output = PROMPT_MOVIE_NOT_FOUND
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("favMovie"))
            else:
                inputVal = movieName
                slot_favMovie.value = inputVal
                speak_output = "Alright! I will try to recommend films similar to {}. ".format(inputVal)
                responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            
        elif setupPhase == 4:
            actorID = getActressId(slot_favActor.value)
            actorName = getActressName(actorID)
            if actorID == 0:
                speak_output = SENTENCE_ACTOR_NOT_FOUND.format(slot_favActor.value)
                prompt_output = PROMPT_ACTOR_NOT_FOUND
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("favActor"))
            else:
                inputVal = actorName
                slot_favActor.value = inputVal
                speak_output = "Okay, I will try to recommend films with {}. ".format(inputVal)
                responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            
        elif setupPhase == 5:
            resolution = slot_favGenre.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                resolvedSlotID = resolution.values[0].value.id #this is already the API-ready genre ID
                inputVal = resolvedSlotName
                slot_favGenre.value = inputVal
                if inputVal == "TV Movie": #edge case: We don't want to say "more TV Movie movies". Yes, this is unnecessary overengineering. No, I don't care.
                    speak_output = "Cool! I will try to recommend more TV Movies to you. "
                else:
                    speak_output = "Cool! I will try to recommend more {} movies to you. ".format(inputVal)
                responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            else:
                speak_output = SENTENCE_GENRE_NOT_FOUND.format(slot_favGenre.value)
                prompt_output = PROMPT_GENRE_NOT_FOUND
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("favGenre"))
            
        elif setupPhase == 6:
            resolution = slot_dislikedGenre.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                resolvedSlotID = resolution.values[0].value.id #this is already the API-ready genre ID
                inputVal = resolvedSlotName
                slot_dislikedGenre.value = inputVal
                if inputVal == "TV Movie": #same edge case handling as above
                    speak_output = "Good to know, I will try to keep TV Movies out of your recommendations. "
                else:
                    speak_output = "Good to know, I will try to keep {} films out of your recommendations. ".format(inputVal)
                responseBuilder.speak(speak_output).add_directive(DelegateDirective(intent))
            else:
                speak_output = SENTENCE_GENRE_NOT_FOUND.format(slot_dislikedGenre.value)
                prompt_output = PROMPT_GENRE_NOT_FOUND
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("dislikedGenre"))
            
        elif setupPhase == 7:
            resolution = slot_finalConfirmation.resolutions.resolutions_per_authority[0]
            
            if resolution.status.code == StatusCode.ER_SUCCESS_MATCH:
                resolvedSlotName = resolution.values[0].value.name
                inputVal = resolvedSlotName
                slot_finalConfirmation.value = inputVal
                responseBuilder.add_directive(DelegateDirective(intent))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = "Please say Okay to save your profile or Stop to cancel."
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("finalConfirmation"))
                
        else: #setupPhase == 8
            #send everything to Firebase
            #session attribs don't work because somehow the last one will only be available one intent call too late, so we wouldn't have the dislikedGenre here if stored via session attribs.
            if slot_finalConfirmation.value == "Okay":
                userID = handler_input.request_envelope.context.system.user.user_id
                knownUser = check_user_exists_by_id(userID)
                streamers = ([slot_streamer.value], slot_streamer.value.split("|"))["|" in slot_streamer.value]
                if knownUser:
                    u = User(slot_dislikedGenre.value, slot_favActor.value, slot_favMovie.value, userID, "DE", [get_last_watched_movie_by_id(userID), is_last_watched_movie_rated_by_id(userID)], slot_favGenre.value, slot_name.value, get_recommended_movies_by_id(userID), streamers, get_likings_by_id(userID), [""])
                else:
                    u = User(slot_dislikedGenre.value, slot_favActor.value, slot_favMovie.value, userID, "DE", ["", True], slot_favGenre.value, slot_name.value, [""], streamers, {'movie': 0, 'genre': 0, 'acting': 0}, [""])
                add_user(u)
                speak_output = "You're all set up! "
                if not knownUser:
                    speak_output += "To get an overview of what you can ask me, just say: Help."
            else:
                speak_output = "Okay, I will not save your new data to your profile."
            responseBuilder.speak(speak_output)
            
        return responseBuilder.response


class FeedbackIntentHandler(AbstractRequestHandler):
    """Handler for Feedback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("feedbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        request = handler_input.request_envelope.request
        intent = request.intent
        responseBuilder = handler_input.response_builder
        sessionAttribs = handler_input.attributes_manager.session_attributes
        
        #for debugging the mess that is the Python ASK:
        sessionAttribs["stringSlotPythonInput_feedbackAspects"] = str(intent.slots["feedbackAspects"]) # stringified version gives python-style attributes (slot_value instead of slotValue) and sets unset ones to None (those don't show up at all in the JSON version). hasattr seems to best map the stringified version.
        sessionAttribs["stringSlotPythonInput_feedbackGeneral"] = str(intent.slots["feedbackGeneral"])
        attribs = {
            'slotValue': hasattr(intent.slots["feedbackAspects"], 'slotValue'),
            'slot_value': hasattr(intent.slots["feedbackAspects"], 'slot_value')
        }
        if hasattr(intent.slots["feedbackAspects"], 'slot_value') and intent.slots["feedbackAspects"].slot_value is not None:
            attribs['.slot_value.resolutions'] = hasattr(intent.slots["feedbackAspects"].slot_value, 'resolutions')
            if hasattr(intent.slots["feedbackAspects"].slot_value, 'resolutions') and intent.slots["feedbackAspects"].slot_value.resolutions is not None:
                attribs['.slot_value.resolutions.resolutionsPerAuthority'] = hasattr(intent.slots["feedbackAspects"].slot_value.resolutions, 'resolutionsPerAuthority')
                attribs['.slot_value.resolutions.resolutions_per_authority'] = hasattr(intent.slots["feedbackAspects"].slot_value.resolutions, 'resolutions_per_authority')
                if hasattr(intent.slots["feedbackAspects"].slot_value.resolutions, 'resolutions_per_authority'):
                    attribs['.slot_value.resolutions.resolutions_per_authority[0]'] = str(intent.slots["feedbackAspects"].slot_value.resolutions.resolutions_per_authority[0])
            else:
                attribs['.slot_value.resolutions.resolutionsPerAuthority'] = "failed, no .slot_value.resolutions"
                attribs['.slot_value.resolutions.resolutions_per_authority'] = "failed, no .slot_value.resolutions"
        else:
            attribs['.slot_value.resolutions'] = "failed, no .slot_value"
        sessionAttribs["feedbackAspectsAttribs"] = attribs
        
        feedbackGeneralRaw = intent.slots["feedbackGeneral"].value
        
        #if no aspect is given yet, .slotValue isn't there and .value is None... SOMETIMES. Other random times, .slot_value is there. OR .slotValue. Depending on Alexa's mood of the day. I want to speak to the manager, Sir!
        #if one aspect is given, .value exists and .slotValue is:
        #{'type': 'Simple','value': 'writing', 'resolutions': {
        #    'resolutionsPerAuthority': [{'authority': '...', 'status': {'code': 'ER_SUCCESS_MATCH'}, 'values': [{'value': {'name': 'story', 'id': '...'}}]}]
        #}}
        #if multi are given, .value is None and .slotValue is:
        #{'type': 'List', 'values': [
        #    {'type': 'Simple', 'value': 'story', 'resolutions': {
        #        'resolutionsPerAuthority': [{'authority': '...', 'status': {'code': 'ER_SUCCESS_MATCH'}, 'values': [{'value': {'name': 'story', 'id': '...'}}]}]
        #    }},
        #    {'type': 'Simple', 'value': 'score', 'resolutions': {
        #        'resolutionsPerAuthority': [{'authority': '...', 'status': {'code': 'ER_SUCCESS_MATCH'}, 'values': [{'value': {'name': 'music', 'id': '...'}}]}]
        #    }}
        #]}
        
        if hasattr(intent.slots["feedbackAspects"], 'slotValue'):
            feedbackAspectsSyntaxIsMessedUpAgain = True #JS-style syntax
            feedbackAspectsRaw = intent.slots["feedbackAspects"].slotValue
            if feedbackAspectsRaw is None:
                feedbackAspectsIsGiven = False
            else:
                feedbackAspectsIsGiven = True
                if feedbackAspectsRaw['type'] == 'List' or feedbackAspectsRaw['object_type'] == 'List':
                    feedbackAspectsIsMulti = True
                else: #feedbackAspectsRaw['type'] == 'Simple'
                    feedbackAspectsIsMulti = False
        elif hasattr(intent.slots["feedbackAspects"], 'slot_value'):
            feedbackAspectsSyntaxIsMessedUpAgain = False #python-style syntax
            feedbackAspectsRaw = intent.slots["feedbackAspects"].slot_value
            if feedbackAspectsRaw is None:
                feedbackAspectsIsGiven = False
            else:
                feedbackAspectsIsGiven = True
                #feedbackAspectsRaw.type == 'List' does not work, because that would be too easy I guess.
                if feedbackAspectsRaw.object_type == 'List':
                    feedbackAspectsIsMulti = True
                else: #feedbackAspectsRaw.object_type == 'Simple'
                    feedbackAspectsIsMulti = False
        else:
            feedbackAspectsSyntaxIsMessedUpAgain = True
            feedbackAspectsRaw = intent.slots["feedbackAspects"].value
            feedbackAspectsIsMulti = False
            if feedbackAspectsRaw is None:
                feedbackAspectsIsGiven = False
            else:
                feedbackAspectsIsGiven = True
        
        #check where we are in the feedback dialog:
        # 0 = no info given yet, need to get feedbackGeneral first
        # 1 = feedbackGeneral is given and to be processed, but we have yet to get feedbackAspects
        # 2 = feedbackGeneral and feedbackAspects are given, feedbackAspects has yet to be processed
        # 3 = we have all we need, so we can give some confirmation and move on.
        feedbackPhase = 0
        if request.dialog_state == DialogState.STARTED:
            if feedbackGeneralRaw is None:
                feedbackPhase = 0
            else:
                feedbackPhase = 1
        elif request.dialog_state == DialogState.IN_PROGRESS:
            if feedbackGeneralRaw is None: ##
                feedbackPhase = 0 ##
            elif not feedbackAspectsIsGiven:
                feedbackPhase = 1
            else:
                feedbackPhase = 2
        else: #request.dialog_state == DialogState.COMPLETED
            feedbackPhase = 3
            
        
        
        if feedbackPhase == 0: #prompt feedbackGeneral slot automatically
            responseBuilder.add_directive(DelegateDirective())
            
        elif feedbackPhase == 1: #we have feedbackGeneral, let's parse it and prompt feedbackAspects
            #process feedbackGeneralRaw
            isFeedbackPositive = isSentimentPositive(str(feedbackGeneralRaw))
            #store the canonical, simplified version of the feedback in the intent for later use
            intent.slots["feedbackGeneral"].value = (FEEDBACK_NEGATIVE, FEEDBACK_POSITIVE)[isFeedbackPositive]
            
            speak_output = (SENTENCE_FEEDBACK_WAS_NEGATIVE,SENTENCE_FEEDBACK_WAS_POSITIVE)[isFeedbackPositive]
            prompt_output = PROMPT_FEEDBACK_ASPECTS.format(("didn't", "did")[isFeedbackPositive], "it")
            responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("feedbackAspects", intent))
            
        elif feedbackPhase == 2:
            #resolve slots: try to match feedbackAspectsRaw to a canonical slot name
            slotResolutions = []
            if feedbackAspectsIsMulti == True:
                if feedbackAspectsSyntaxIsMessedUpAgain:
                    allvalues = feedbackAspectsRaw['values']
                    for val in allvalues:
                        slotResolutions.append({
                            "orig": val['value'],
                            "resolution": val['resolutions']['resolutionsPerAuthority'][0]
                        })
                else:
                    allvalues = feedbackAspectsRaw.values
                    for val in allvalues:
                        slotResolutions.append({
                            "orig": val.value,
                            "resolution": val.resolutions.resolutions_per_authority[0]
                        })
            else:
                if feedbackAspectsSyntaxIsMessedUpAgain:
                    slotResolutions.append({
                        "orig": feedbackAspectsRaw['value'],
                        "resolution": feedbackAspectsRaw['resolutions']['resolutionsPerAuthority'][0]
                    })
                else:
                    slotResolutions.append({
                        "orig": feedbackAspectsRaw.value, #['value'] tested, does not work. for reasons.
                        "resolution": feedbackAspectsRaw.resolutions.resolutions_per_authority[0]
                    })
            
            resolvedToSave = []
            unresolvedToSave = []
            if feedbackAspectsSyntaxIsMessedUpAgain:
                for val in slotResolutions:
                    if val['resolution']['status']['code'] == 'ER_SUCCESS_MATCH':
                        resolvedToSave.append(val['resolution']['values'][0]['value']['name']) #resolved to canonical slot value
                    else:
                        if(val['orig'] != 'the'): #sometimes, e.g. when saying "the writing and the cast", Alexa will fill the slots with "writing", "the" and "cast". It can't resolve "the", so throw all the "the"s out here.
                            unresolvedToSave.append(val['orig']) #unresolved
            else:
                for val in slotResolutions:
                    if val['resolution'].status.code == StatusCode.ER_SUCCESS_MATCH:
                        resolvedToSave.append(val['resolution'].values[0].value.name) #resolved to canonical slot value
                    else:
                        if(val['orig'] != 'the'): #sometimes, e.g. when saying "the writing and the cast", Alexa will fill the slots with "writing", "the" and "cast". It can't resolve "the", so throw all the "the"s out here.
                            unresolvedToSave.append(val['orig']) #unresolved
            
            handler_input.attributes_manager.session_attributes["resolvedMovieAspects"] = resolvedToSave
            handler_input.attributes_manager.session_attributes["unresolvedMovieAspects"] = unresolvedToSave
            
            if len(resolvedToSave)>0:
                #intent.slots["feedbackAspects"].value = str(resolvedToSave)
                userID = handler_input.request_envelope.context.system.user.user_id
                update_likings_by_id(userID, {
                    "acting": ("acting" in resolvedToSave),
                    "genre": ("genre" in resolvedToSave),
                    "movie": ("movie" in resolvedToSave)
                })
                responseBuilder.add_directive(DelegateDirective(intent))
            else:
                speak_output = SENTENCE_DID_NOT_UNDERSTAND
                prompt_output = PROMPT_FEEDBACK_ASPECTS.format(("didn't", "did")[intent.slots["feedbackGeneral"].value is FEEDBACK_POSITIVE], "the recommendation")
                responseBuilder.speak(speak_output+prompt_output).ask(prompt_output).add_directive(makeESDir("finalConfirmation"))
            
            #responseBuilder.add_directive(DelegateDirective(intent))
            
        else: # feedbackPhase == 3; we have all feedback values and can move on.
            userID = handler_input.request_envelope.context.system.user.user_id
            rate_last_watched_movie_by_id(userID, (feedbackGeneralRaw==FEEDBACK_POSITIVE))
            #aspects = intent.slots["feedbackAspects"].value
            #update_likings_by_id(userID, {
            #    "acting": ("acting" in aspects),
            #    "genre": ("genre" in aspects),
            #    "movie": ("movie" in aspects)
            #})
            
            speak_output = SENTENCE_FEEDBACK_ACCEPTED
            responseBuilder.speak(speak_output)
                
            
        return responseBuilder.response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "To get a recommendation, you can just say: Recommend something. You can also request films similar to a given film, from a specific genre or with an actor or actress of your choice. To let me pick a good rewatch, just say: Recommend a rewatch. To change your profile, just say: Setup."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Cancelling."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(RecommendationIntentHandler())
sb.add_request_handler(RecommendationByMovieIntentHandler())
sb.add_request_handler(RecommendationByActorIntentHandler())
sb.add_request_handler(RecommendationByGenreIntentHandler())
sb.add_request_handler(RecommendationRewatchIntentHandler())
sb.add_request_handler(SetupIntentHandler())
sb.add_request_handler(FeedbackIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()