import json
import requests
# import const
import sqlite3
import random
import time


SQL_DB_PATH=r"D:\Downloads\train\train\train_databases\train_databases\cars\cars.sqlite"
output_data = []
correct_output_data = []
incorrect_output_data = []
    
# Database Interaction Module
def connect_to_database():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(SQL_DB_PATH)

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
def evaluate_answers(question,llm_answer_dict, correct_answer, conn):
    """
    Compares the LLM's answer with the correct answer, saves the details to 
    output_data, and returns the comparison result
    """
    examples = llm_answer_dict['examples']
    similarity_scores = llm_answer_dict["similarity_scores"]
    llm_answer = llm_answer_dict['model_response']

    if llm_answer_dict['is_valid_syntax'] == True:
        try:
            llm_results = execute_query(conn, llm_answer)
        except Exception:
            llm_results = "Error"
    else:
        llm_results = "Invalid Syntax"


    correct_results = execute_query(conn, correct_answer)

    # Append results to output_data

    output = {
        "question": question,
        "llm_answer": llm_answer,
        "llm_results": llm_results,
        "correct_answer": correct_answer,
        "correct_results": correct_results,
        "examples": examples,
        "similarity_scores": similarity_scores,
    }
    
    output_data.append(output)

    if llm_results == correct_results:
        correct_output_data.append(output)
    else:
        incorrect_output_data.append(output)

    return llm_results == correct_results


def save_output_data(output_data):
    """Saves the output data to a JSON file."""
    with open('sql_bot/metrics/output_results.json', 'w') as f:
        json.dump(output_data, f, indent=4)

def save_correct_data(correct_data):
    """Saves the correct data to a JSON file."""
    with open('sql_bot/metrics/correct_output_data.json', 'w') as f:
        json.dump(correct_data, f, indent=4)

def save_incorrect_data(incorrect_data):
    """Saves the incorrect data to a JSON file."""
    with open('sql_bot/metrics/incorrect_output_data.json', 'w') as f:
        json.dump(incorrect_data, f, indent=4)
    

# Main Execution
if __name__ == "__main__":
    with open('sql_bot/metrics/cars.json', 'r') as f:
        data = json.load(f)

    # Select 30 random questions
    random.shuffle(data)  # Shuffle the data in-place
    data = data[:3]

    correct = 0
    total = len(data)

    conn = connect_to_database()

    start_time = time.time()

    for element in data:
        question = element['question']
        correct_answer = element['SQL']

        llm_answer = send_question_to_llm(question)
        if llm_answer:
            if evaluate_answers(question,llm_answer, correct_answer, conn):
                correct += 1

    conn.close()

    end_time = time.time()
    # Save output data to JSON file

    save_output_data(output_data)
    save_correct_data(correct_output_data)
    save_incorrect_data(incorrect_output_data)



    print(f"Total time taken: {end_time - start_time} seconds")
    print(f"Correct: {correct}")
    accuracy_percentage = (correct / total) * 100
    print(f"Accuracy: {accuracy_percentage:.2f}")
