from flask import Flask, render_template, request, session, jsonify
import os
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import re
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'
load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

df=pd.read_csv("static/data.csv", encoding='unicode_escape')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard', methods=['POST'])
def dashboard():
    user_query = request.form.get('query')
    session['user_query'] = user_query
    session['processing'] = True
    return render_template('dashboard.html')
    
@app.route('/get_chart_code', methods=['GET'])
def get_chart_code():
    user_query = session.get('user_query')
    if not user_query or not session.get('processing'):
        return jsonify({'error': 'No query or processing not started'}), 400

    print("Calling LLM")
    columns = df.columns.values.tolist()
    buffer = io.StringIO()

    df.info(buf=buffer)

    info_string = buffer.getvalue()
    info_lines = info_string.splitlines()
    filtered_info = "\n".join(line for line in info_lines if "<class 'pandas.core.frame.DataFrame'>" not in line)
    prompt_template = f"""
    Write COMPLETE chartjs code in html to create a profession interactive dashboard for analyst to analyse and visualize all data for following user query: {user_query}.
    Use the data stored in file 'static/data.csv' which has following information: {filtered_info}.\n\n
    First load the csv using papaparse and use it to create dashboard.
    Dashboard components should have all types of charts, tables, gauges, metrics, and other components.Try to use all the components in responsive manner.
    While writing code for Gauge chart please remember rotation and circumference options are in degrees and use green and light grey colors to give sense of gauge chart also show labels and values in it.
    Table should be beautiful and responsive vertically and horizontally with pagination feature with left right button at there bottom corners and should have 5 rows per page.
    All the components should be interactive and have all tools.
    Apply dark theme to complete page.
    Use colors to make charts attractive and visualizable.
    Use white color for all the text and labels of charts.
    All charts should be responsive and placed properly.
    Table should be at the bottom.
    Code should be correct and valid.
    Return only a complete code. 
    Follow all the steps carefully.
    """
    

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-exp-0827", temperature=0.3)
    response = llm.invoke(prompt_template).content
    #print(response)
    pattern = r'```(html)?(.*?)```'
    match = re.findall(pattern, response, re.DOTALL)
    code = "\n".join([block[1] for block in match])
    #print(code)

    session['chart_code'] = code
    session['processing'] = False
    return jsonify({'chart_code': code})

if __name__ == '__main__':
    app.run()
