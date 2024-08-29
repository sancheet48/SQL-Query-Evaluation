# import json
# import requests
# # import const
# import sqlite3
# import random
# import time


# SQL_DB_PATH=r"D:\Downloads\train\train\train_databases\train_databases\cars\cars.sqlite"
# output_data = []
# correct_output_data = []
# incorrect_output_data = []
    
# # Database Interaction Module
# def connect_to_database():
#     """Establishes a connection to the SQLite database."""
#     return sqlite3.connect(SQL_DB_PATH)

# def execute_query(conn, query):
#     """Executes a query on the given database connection."""
#     cursor = conn.cursor()
#     cursor.execute(query)
#     results = cursor.fetchall()
#     return results

# # LLM Interaction Module
# def send_question_to_llm(question):
#     """Sends a question to the LLM endpoint and returns the response."""
#     url = "http://localhost:8000/api/v1/bot/query"
#     headers = {"Content-Type": "application/json"}
#     data = {"query": question}

#     response = requests.post(url, headers=headers, json=data)

#     if response.status_code == 200:
#         return response.json()
#     else:
#         print("Error:", response.status_code)
#         return None

# # Evaluation Module
# def evaluate_answers(question,llm_answer_dict, correct_answer, conn):
#     """
#     Compares the LLM's answer with the correct answer, saves the details to 
#     output_data, and returns the comparison result
#     """
#     examples = llm_answer_dict['examples']
#     similarity_scores = llm_answer_dict["similarity_scores"]
#     llm_answer = llm_answer_dict['model_response']

#     if llm_answer_dict['is_valid_syntax'] == True:
#         try:
#             llm_results = execute_query(conn, llm_answer)
#         except Exception:
#             llm_results = "Error"
#     else:
#         llm_results = "Invalid Syntax"


#     correct_results = execute_query(conn, correct_answer)

#     # Append results to output_data

#     output = {
#         "question": question,
#         "llm_answer": llm_answer,
#         "llm_results": llm_results,
#         "correct_answer": correct_answer,
#         "correct_results": correct_results,
#         "examples": examples,
#         "similarity_scores": similarity_scores,
#     }
    
#     output_data.append(output)

#     if llm_results == correct_results:
#         correct_output_data.append(output)
#     else:
#         incorrect_output_data.append(output)

#     return llm_results == correct_results


# def save_output_data(output_data):
#     """Saves the output data to a JSON file."""
#     with open('sql_bot/metrics/output_results.json', 'w') as f:
#         json.dump(output_data, f, indent=4)

# def save_correct_data(correct_data):
#     """Saves the correct data to a JSON file."""
#     with open('sql_bot/metrics/correct_output_data.json', 'w') as f:
#         json.dump(correct_data, f, indent=4)

# def save_incorrect_data(incorrect_data):
#     """Saves the incorrect data to a JSON file."""
#     with open('sql_bot/metrics/incorrect_output_data.json', 'w') as f:
#         json.dump(incorrect_data, f, indent=4)
    

# # Main Execution
# if __name__ == "__main__":
#     with open('sql_bot/metrics/cars.json', 'r') as f:
#         data = json.load(f)

#     # Select 30 random questions
#     random.shuffle(data)  # Shuffle the data in-place
#     data = data[:3]

#     correct = 0
#     total = len(data)

#     conn = connect_to_database()

#     start_time = time.time()

#     for element in data:
#         question = element['question']
#         correct_answer = element['SQL']

#         llm_answer = send_question_to_llm(question)
#         if llm_answer:
#             if evaluate_answers(question,llm_answer, correct_answer, conn):
#                 correct += 1

#     conn.close()

#     end_time = time.time()
#     # Save output data to JSON file

#     save_output_data(output_data)
#     save_correct_data(correct_output_data)
#     save_incorrect_data(incorrect_output_data)



#     print(f"Total time taken: {end_time - start_time} seconds")
#     print(f"Correct: {correct}")
#     accuracy_percentage = (correct / total) * 100
#     print(f"Accuracy: {accuracy_percentage:.2f}")


import json
import requests
import sqlite3
import random
import time
import const




class DatabaseManager:
    """Handles interactions with the SQLite database."""

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Establishes a connection to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

    def execute_query(self, query):
        """Executes a query on the database and returns the results."""
        cursor = self.conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        return results


class LLMClient:
    """Handles interactions with the LLM API."""

    def __init__(self, url):
        self.url = url

    def send_question(self, question):
        """Sends a question to the LLM endpoint and returns the response."""
        headers = {"Content-Type": "application/json"}
        data = {"query": question}

        response = requests.post(self.url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            print("Error:", response.status_code)
            return None


class Evaluator:
    """Evaluates the LLM's answers and handles the output data."""

    def __init__(self):
        self.output_data = []
        self.correct_output_data = []
        self.incorrect_output_data = []

    def evaluate_answer(self, question, llm_answer_dict, correct_answer, db_manager):
        """
        Compares the LLM's answer with the correct answer, saves the details to output_data,
        and returns the comparison result.
        """
        examples = llm_answer_dict['examples']
        similarity_scores = llm_answer_dict["similarity_scores"]
        llm_answer = llm_answer_dict['model_response']

        if llm_answer_dict['is_valid_syntax']:
            try:
                llm_results = db_manager.execute_query(llm_answer)
            except Exception:
                llm_results = "Error"
        else:
            llm_results = "Invalid Syntax"

        correct_results = db_manager.execute_query(correct_answer)

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

        self.output_data.append(output)

        if llm_results == correct_results:
            self.correct_output_data.append(output)
        else:
            self.incorrect_output_data.append(output)

        return llm_results == correct_results

    def save_output_data(self, filename, data):
        """Saves the output data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def save_all_data(self):
        """Saves all data categories to respective JSON files."""
        self.save_output_data('sql_bot/metrics/output_results.json', self.output_data)
        self.save_output_data('sql_bot/metrics/correct_output_data.json', self.correct_output_data)
        self.save_output_data('sql_bot/metrics/incorrect_output_data.json', self.incorrect_output_data)


def main():
    """Main function to run the evaluation process."""
    # Load questions and correct answers
    with open('sql_bot/metrics/cars.json', 'r') as f:
        data = json.load(f)

    # Shuffle and select 30 random questions
    random.shuffle(data)
    data = data[:5]

    # Initialize components
    db_manager = DatabaseManager(const.SQL_DB_PATH)
    db_manager.connect()
    llm_client = LLMClient("http://localhost:8000/api/v1/bot/query")
    evaluator = Evaluator()

    correct = 0
    total = len(data)
    start_time = time.time()

    for element in data:
        question = element['question']
        correct_answer = element['SQL']

        llm_answer = llm_client.send_question(question)
        if llm_answer:
            if evaluator.evaluate_answer(question, llm_answer, correct_answer, db_manager):
                correct += 1

    db_manager.close()
    end_time = time.time()

    # Save output data to JSON files
    evaluator.save_all_data()

    print(f"Total time taken: {end_time - start_time} seconds")
    print(f"Correct: {correct}")
    accuracy_percentage = (correct / total) * 100
    print(f"Accuracy: {accuracy_percentage:.2f}")


if __name__ == "__main__":
    main()
