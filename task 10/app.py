import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
app = Flask(__name__)
llm = ChatGroq(
    groq_api_key=API_KEY,
    model_name='llama3-8b-8192',
    temperature=0.7
)
template = """
You are a helpful hotel concierge. Answer user questions clearly and concisely about hotel details (rooms, pricing, amenities, location).
If the question is outside those topics, respond politely that you can only help with hotel info.
User: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
parser = StrOutputParser()
chain = (
    {"question": RunnablePassthrough()}
    | prompt
    | llm
    | parser
)
@app.route('/')
def home():
    return render_template('chat.html')
@app.route('/ask', methods=['POST'])
def ask():
    user_msg = request.json.get('message', '')
    answer = chain.invoke(user_msg)
    return jsonify({'response': answer})
if __name__ == '__main__':
    app.run(debug=True)