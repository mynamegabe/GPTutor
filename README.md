# GPTutor
A Top 8 NUS Hack&Roll Project

https://devpost.com/software/gptutor

### Dependencies
```console
pip3 install -r requirements.txt
```

### Usage
The application uses the GPT3 API to send prompts and receive responses. This requires your OpenAI API Key as it will spend tokens when making requests to the API, specifically using the davinci model which costs $0.02/1000 tokens. To set the API key, save the API key into an environment variable named "OPENAI_KEY". 

```console
export OPENAI_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
python3 app.py
```
