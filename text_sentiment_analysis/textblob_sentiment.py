'''
code with limited words analysis
'''

from textblob import TextBlob
def get_sentiment(input_text: str) -> str:
    """
    Analyzes the sentiment of a given text.

    Args:
        input_text: The string to be analyzed.

    Returns:
        'positive', 'negative', or 'neutral'.
    """
    if not input_text.strip():
        return 'neutral'

    analysis = TextBlob(input_text)
    polarity = analysis.sentiment.polarity    
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'