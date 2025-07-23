import os
import pandas as pd
from sqlalchemy import create_engine, text
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_ollama import OllamaLLM
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
# FIX 1: Import render_template to serve the HTML page
from flask import Flask, request, jsonify, render_template

# --- 1. SETUP: Create Flask app and configure the database ---
app = Flask(__name__)
DB_PATH = "sqlite:///ecommerce.db"
engine = create_engine(DB_PATH)
db = SQLDatabase(engine=engine)

# Create a directory for saving charts if it doesn't exist
if not os.path.exists("static/images"):
    os.makedirs("static/images")

# --- 2. DATA LOADING: Load your specific CSV files into the SQL database ---
def setup_database():
    files = {
        'ad_sales': 'data/ad_sales.csv',
        'total_sales': 'data/total_sales.csv',
        'eligibility': 'data/eligibility.csv'
    }
    
    with engine.connect() as conn:
        for table_name, file_path in files.items():
            res = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"))
            if res.fetchone() is None:
                print(f"Creating table: {table_name}")
                df = pd.read_csv(file_path, encoding='cp1252')
                df.columns = [col.strip().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]
                df.to_sql(table_name, engine, index=False)
            else:
                print(f"Table '{table_name}' already exists.")

# --- 3. AI LOGIC: Connect the LLM to the database for Text-to-SQL ---
llm = OllamaLLM(model="llama3") 
generate_query_chain = create_sql_query_chain(llm, db)
answer_prompt = PromptTemplate.from_template(
    """Given the user's question and the result of an SQL query, provide a clear, friendly, human-readable answer.
    Summarize the result and present it directly.
    
    Here are some key business rules for your answer:
    - RoAS (Return on Ad Spend) is calculated as ad_sales / ad_spend.
    - CPC (Cost Per Click) is calculated as ad_spend / clicks.
    - The tables are linked by the 'item_id' column.

    Question: {question}
    SQL Result: {result}
    Answer:
    """
)
answer_chain = answer_prompt | llm | StrOutputParser()

# --- 4. API & UI ENDPOINTS ---

# FIX 2: Add a new route to serve the user interface
@app.route('/')
def home():
    """Serves the main HTML user interface."""
    return render_template('index.html')

# This is the existing API endpoint that the UI will call
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "A question is required."}), 400

    try:
        sql_query = generate_query_chain.invoke({"question": question})
        sql_query = sql_query.strip().replace("```sql", "").replace("```", "")
        print(f"Generated SQL Query: {sql_query}")

        with engine.connect() as conn:
            result = conn.execute(text(sql_query)).fetchall()
        print(f"Query Result: {result}")
        
        final_answer = answer_chain.invoke({"question": question, "result": result})
        
        return jsonify({"answer": final_answer, "sql_query": sql_query})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

# --- 5. MAIN EXECUTION ---
if __name__ == '__main__':
    setup_database()
    app.run(debug=True, port=5001)
