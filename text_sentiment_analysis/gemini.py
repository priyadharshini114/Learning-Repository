'''
code with gemini-API words analysis
'''

import os
import google.generativeai as genai
try:
    genai.configure(api_key="api_key") 
except Exception as e:
    print(f"Error during API key configuration: {e}")
    exit()
model = genai.GenerativeModel('gemini-1.5-flash')

def get_sentiment(input_text: str) -> str:
    """
    Analyzes the sentiment of a given text using Google's Gemini LLM.
    """
    if not input_text.strip():
        return 'neutral'

    prompt = f"""
    Analyze the sentiment of the following text. The text may be sarcastic or nuanced.
    Respond with only a single word: 'positive', 'negative', or 'neutral'.
    
    Text: "{input_text}"
    """

    try:
        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        
        if result in ['positive', 'negative', 'neutral']:
            return result
        else:
            print(f"Warning: LLM returned an unexpected value: '{result}'")
            return 'neutral'

    except Exception as e:
        print(f"Error calling the Gemini API: {e}")
        return 'neutral'