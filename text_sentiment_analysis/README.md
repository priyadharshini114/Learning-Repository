# Talk to Pooh — Sentiment-Based Interactive App

This is a sentiment analysis-based interactive application that changes Winnie the Pooh's mood (image) based on the user's input. It supports multiple sentiment engines (Gemini API, Gemini with translation, or a simple offline model).

---
##  Project Structure

├── main_app.py # Main GUI app (Tkinter)
├── gemini.py # Sentiment using Gemini API
├── gemini_translator.py # Gemini + Google Translate for multilingual support
├── sentiment.py # Offline sentiment analysis using TextBlob
├── pooh.png # Happy Pooh image
├── sad_pooh.png # Sad Pooh image
├── main_pic.gif # Neutral Pooh image


---
## How to Run

### 1. Install Dependencies

```
! pip install google-generativeai googletrans==4.0.0-rc1 Pillow textblob nest_asyncio

```
or
```
    pip install -r requirements.txt

```

```
    python -m textblob.download_corpora
```
### Run the App 
    ```
    python main_app.py
    ```

python main_app.py
Switch Sentiment Engine

### By default, the app uses:

Edit
```
    from gemini import get_sentiment
```
You can switch to another engine by modifying the import in main_app.py:

For Gemini + Translator:

Edit
```
    from gemini_translator import get_sentiment
```
For Offline TextBlob model:


Edit
```
    from simple_sentiment import get_sentiment  
```

### Features
GUI-based sentiment interaction with Pooh

Detects and analyzes sarcasm (via Gemini)

Supports multilingual input with auto-translation

Offline mode using TextBlob (no API key required)

### Note on API Keys
Update your gemini.py and gemini_translator.py with your actual Google Gemini API Key in:
```
    genai.configure(api_key="YOUR_API_KEY")
```

### Tags
#Python #SentimentAnalysis #GeminiAPI #Tkinter #LLM #PoohApp #GoogleTranslate #MultilingualAI