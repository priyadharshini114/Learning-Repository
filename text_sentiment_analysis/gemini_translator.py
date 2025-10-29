'''
code with gemini-API words analysis along with lagauge detector and convert to englishs

'''
import os
import google.generativeai as genai
from googletrans import Translator
import asyncio
import nest_asyncio 

nest_asyncio.apply()
try:
    genai.configure(api_key="API_KEY")
except Exception as e:
    print(f"Error during API key configuration: {e}")
    exit()

model = genai.GenerativeModel('gemini-1.5-flash')
translator = Translator()



async def async_process_and_get_sentiment(input_text: str) -> str:
    """
    This is an asynchronous function to handle translation and sentiment analysis.
    """
    processed_text = input_text
    
    try:
        detection = await translator.detect(input_text)
        lang_code = detection.lang

        if lang_code != 'en':
            print(f"Detected language: {lang_code}. Translating to English...")
            translation = await translator.translate(input_text, dest='en')
            processed_text = translation.text
            print(f"Translated text: '{processed_text}'")
        else:
            print("Detected language: English. No translation needed.")
        
        prompt = f"""
        Analyze the sentiment of the following text. The text may be sarcastic or nuanced.
        Respond with only a single word: 'positive', 'negative', or 'neutral'.
        
        Text: "{processed_text}"
        """

        response = model.generate_content(prompt)
        result = response.text.strip().lower()
        
        if result in ['positive', 'negative', 'neutral']:
            return result
        else:
            print(f"Warning: LLM returned an unexpected value: '{result}'")
            return 'neutral'

    except Exception as e:
        print(f"An error occurred: {e}")
        return 'neutral'

def get_sentiment(input_text: str) -> str:
    """
    A synchronous wrapper that runs our async function.
    """
    if not input_text.strip():
        return 'neutral'
    
    return asyncio.run(async_process_and_get_sentiment(input_text))