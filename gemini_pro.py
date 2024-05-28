import os 
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

import google.generativeai as genai
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')


def response(prompt):
    response = model.generate_content(prompt)
    return response.text