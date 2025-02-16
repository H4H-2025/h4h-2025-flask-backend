from app import app

client = Groq(api_key="you-thought-lil-boi")

@app.route('/', methods=['GET'])
def home_page():
    return {'message': 'Hello, World!'}
