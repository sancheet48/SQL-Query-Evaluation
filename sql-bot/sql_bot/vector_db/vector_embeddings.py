"""Function to create Vector DB."""
import argparse
import os
import shutil
import json

import chromadb
from chromadb.config import Settings
from vector_db_models import EMBEDDING_FUNCTION


def create_vector_db(
    filepath: str,
    vector_db_path: str,
):
    """Create Vector DB from sql DB.


    Args:
        connection_string (str): The connection string for the sqlDB.
        db_name (str): The name of the sqlDB database.
        collection_name (str): The name of the sqlDB collection.
        vector_db_path (str): The path to store the vector DB.
    """
    if os.path.isdir(vector_db_path):
        print("Removing existing vector db path.")
        shutil.rmtree(vector_db_path)


    with open(filepath, 'r') as f:
        data = json.load(f)


    sql_documents_input = []
    sql_documents_response = []


    for ele in data:


        response_dict = {}  # since the metadata has to be dict or None


        response_dict["response"] = ele["SQL"]
        sql_documents_input.append(ele["question"])
        sql_documents_response.append(response_dict)


    print("Computing Vectors")
    chroma_client = chromadb.PersistentClient(
        path=vector_db_path,
        settings=Settings(allow_reset=True, anonymized_telemetry=False),
    )
    chat_collection = chroma_client.create_collection(
        name="chat_collection", embedding_function=EMBEDDING_FUNCTION
    )
    ids = [str(i) for i in range(len(sql_documents_input))]


    chat_collection.add(
        documents=sql_documents_input,
        metadatas=sql_documents_response,
        ids=ids,
    )


    print(f"Embedding are succesfully stored in {vector_db_path}")




def main():
    """Create Vector DB."""
    parser = argparse.ArgumentParser(
        description="Create vector database from sqlDB."
    )
    parser.add_argument(
        "--filepath", required=True, help="sqlDB connection string."
    )
    
    parser.add_argument(
        "--vector_db_path", required=True, help="Vector DB Path."
    )


    args = parser.parse_args()


    create_vector_db(
        args.filepath,
        args.vector_db_path,
    )




if __name__ == "__main__":
    main()