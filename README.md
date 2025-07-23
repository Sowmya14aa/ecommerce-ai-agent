This project is a fully functional AI-powered data agent designed to answer questions about e-commerce data using natural language. It provides a simple, chat-based web interface where a user can ask complex questions like "What were my total sales last week?" or "Which product had the highest Return on Ad Spend (RoAS)?".

The agent leverages a locally-run Large Language Model (Llama 3) via Ollama to understand the user's question and dynamically generate the correct SQL query. This query is then executed on a database containing product sales, advertising metrics, and eligibility data. Finally, the raw data is translated back into a clear, human-readable answer for the user.

The entire application is built with Python, using Flask for the backend API and LangChain to orchestrate the interactions between the LLM and the database. This approach creates a powerful and intuitive way to explore complex data without needing to write any code.
