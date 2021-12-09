# Natural Language Toolkit
# https://www.nltk.org/index.html
import nltk

from nltk.sentiment.vader import SentimentIntensityAnalyzer

# VADER sentiment analysis tools:
# Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for
# Sentiment Analysis of Social Media Text. Eighth International Conference on
# Weblogs and Social Media (ICWSM-14). Ann Arbor, MI, June 2014.



def isSentimentPositive(str):
    # type: (String) -> bool
    analyzer = SentimentIntensityAnalyzer(lexicon_file="vader_lexicon.txt")
    scores = analyzer.polarity_scores(str)
    return (scores['compound'] > 0) #careful: "pretty" is considered rather positive, so "pretty meh" leans positive while "pretty bad" stays negative. "super" can even turn "super bad" positive. Same if you talk e.g. about how you "can't understand the super amazing reviews".
