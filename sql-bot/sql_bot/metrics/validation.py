import json
import requests
import const
import sqlite3
import random

# Database Interaction Module
def connect_to_database():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(const.SQL_DB_PATH)

def execute_query(conn, query):
    """Executes a query on the given database connection."""
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    return results

# LLM Interaction Module
def send_question_to_llm(question):
    """Sends a question to the LLM endpoint and returns the response."""
    url = "http://localhost:8000/api/v1/bot/query"
    headers = {"Content-Type": "application/json"}
    data = {"query": question}

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)
        return None

# Evaluation Module
def evaluate_answers(llm_answer, correct_answer, conn, output_data):
    """
    Compares the LLM's answer with the correct answer, saves the details to 
    output_data, and returns the comparison result
    """
    if llm_answer['is_valid_syntax'] == True:
            
        try:
            llm_answer = llm_answer['model_response']
            llm_results = execute_query(conn, llm_answer)
        except Exception as e:
            llm_results = "Error"
            #print(e)
    else:
        llm_results = "Invalid Syntax"


    correct_results = execute_query(conn, correct_answer)

    # Append results to output_data
    output_data.append({
        "question": question,
        "llm_answer": llm_answer,
        "llm_results": llm_results,
        "correct_answer": correct_answer,
        "correct_results": correct_results
    })

    return llm_results == correct_results

# Main Execution
if __name__ == "__main__":
    with open('cars.json', 'r') as f:
        data = json.load(f)

    # Select 30 random questions
    random.shuffle(data)  # Shuffle the data in-place
    data = data[:10]

    correct = 0
    total = len(data)

    conn = connect_to_database()

    # Initialize list to store output data
    output_data = []

    for element in data:
        question = element['question']
        correct_answer = element['SQL']

        llm_answer = send_question_to_llm(question)
        if llm_answer:
            if evaluate_answers(llm_answer, correct_answer, conn, output_data):
                correct += 1

    conn.close()

    # Save output data to JSON file
    with open('output_results.json', 'w') as f:
        json.dump(output_data, f, indent=4)

    print(f"Correct: {correct}")
    accuracy_percentage = (correct / total) * 100
    print(f"Accuracy: {accuracy_percentage:.2f}")