"""Query BOT module."""
import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from time import time
import chromadb
from chromadb.config import Settings
from fastapi.responses import JSONResponse
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import const
from sql_bot.lib import output_modifier
from sql_bot.lib.llm_models import LLM_MODEL
from sql_bot.vector_db.vector_db_models import EMBEDDING_FUNCTION
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__file__)



LLM_TEMPLATE = (
    "### System: \n You are a helpful assistant to convert text to "
    + "SQL query.Answer exactly in one line from the schema. "
    + "Generate a single SQL query for the question from schema below : "
    + "{schema} "
    + "\n### User: \n{question}"
    + "\n### Assistant:\n "
)


LLM_SCHEMA = None
CHAT_COLLECTION = None

LLM_PROMPT = PromptTemplate(
    template=LLM_TEMPLATE, input_variables=["question", "schema"]
)
LLM_CHAIN = LLMChain(prompt=LLM_PROMPT, llm=LLM_MODEL)
# LLM_CHAIN = LLMChain(prompt=LLM_PROMPT | LLM_MODEL



def startup():
    """Startup function validator."""
    global LLM_SCHEMA, CHAT_COLLECTION
    if not const.CHROMA_DB_PATH:
        logger.warning(
            "Environment variables: 'CHROMA_DB_PATH' not defined. "
            + "Examples will not be added in prompt.",
        )
    if not const.SERVICE_COM_TOKEN:
        logger.warning(
            "Environment variable 'SERVICE_COM_TOKEN' not set, "
            + "token check will be disabled"
        )
    if not os.path.isfile(const.LLM_SCHEMA_PATH):
        logger.error(f"'{const.LLM_SCHEMA_PATH}' file not found")
        sys.exit(-1)
    logger.info("Loading LLM Schema")
    with open(const.LLM_SCHEMA_PATH) as file_p:
        LLM_SCHEMA = file_p.read()


    if const.CHROMA_DB_PATH:
        if not os.path.isdir(const.CHROMA_DB_PATH):
            logger.error("'%s' directory not found", const.CHROMA_DB_PATH)
            sys.exit(-1)


        chroma_client = chromadb.PersistentClient(
            path=const.CHROMA_DB_PATH,
            settings=Settings(allow_reset=True, anonymized_telemetry=False),
        )
        CHAT_COLLECTION = chroma_client.get_collection(
            name="chat_collection", embedding_function=EMBEDDING_FUNCTION
        )


def shutdown():
    """Teardown function."""
    ...



def retrieve_vdb(query: str) -> tuple:
    """Load the vectordb from local path and return the examples and similarity scores.

    Args:
        query (str): The question to be asked.

    Returns:
        tuple: A tuple containing the examples string and a list of similarity scores.
    """
    if not CHAT_COLLECTION:
        return "", []
    query_result = CHAT_COLLECTION.query(query_texts=query, n_results=4)

    output_string = ""
    similarity_scores = []

    for document, metadata, distance in zip(
        query_result["documents"][0], 
        query_result["metadatas"][0], 
        query_result["distances"][0]
    ):
        input_text = document
        response = metadata["response"]
        output_string += (
            f"{{\n"
            f"    'question': '{input_text}',\n"
            f"    'sql_query': '{response}'\n"
            f"}},\n"
        )
        similarity_scores.append(1 - distance)  # Convert distance to similarity score

    # Removing the trailing comma and newline
    output_string = output_string.rstrip(",\n")
    return output_string, similarity_scores

def model_output(input_question: str, examples: str, similarity_scores: list) -> dict:
    """Get the corresponding sql query for the input question.

    Args:
        input_question (str): The question to be asked
        examples (str): The examples to be added in the prompt.
        similarity_scores (list): The similarity scores for the examples.

    Returns:
        dict: Gives the answer for the corresponding input query.
    """
    logging.info("User query: '%s'", input_question)
    start_time = time()
    response = LLM_CHAIN.run(
        {"question": input_question, "schema": LLM_SCHEMA + examples}
    )
    time_taken = time() - start_time
    logging.info("LLM response: '%s'", response)
    api_response = get_api_response_template()
    api_response["model_response"] = response
    api_response["time_taken"] = time_taken
    api_response["similarity_scores"] = similarity_scores
    return api_response

def get_api_response_template() -> dict:
    """Get API response template.

    Returns:
        dict: Response template
    """
    return {
        "model_response": "",
        "is_valid_syntax": False,
        "time_taken": 0,
        "examples": "",
        "similarity_scores": [],
    }




def sql_connect(api_response: dict) -> dict:
    """Get list of sytems for the given response.
    Args:
        response (str): Response for the given llm
    Returns:
        list: List of systems having the desired criteria.
    """
    api_response["model_response"] = output_modifier.query_parser(api_response["model_response"])
    api_response["model_response"] = output_modifier.add_case_insensetiveness(api_response["model_response"])
    # api_response["model_response"] = add_distinct(api_response["model_response"])
    api_response["is_valid_syntax"] = output_modifier.validate_sql(api_response["model_response"])

    return api_response


def get_db_query(query: str) -> dict:
    """Get System from query.

    Args:
        query (str): Natural Language Query

    Returns:
        list: List of systems
    """
    examples, similarity_scores = retrieve_vdb(query)

    api_response = model_output(query, examples, similarity_scores)
    api_response["examples"] = examples
    try:
        api_response = sql_connect(api_response)
    except Exception as expt:
        logger.error("Exception: %s", expt)
        return JSONResponse(content=api_response, status_code=400)
    return JSONResponse(content=api_response, status_code=200)

def main():
    """Test functionality manually."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(module)s:%(lineno)d"
        + " | %(message)s",
        handlers=[
            RotatingFileHandler(
                f"{os.path.join(const.PROJECT_DIR, 'bot.log')}",
                maxBytes=256 * 1024,
                backupCount=1,
                encoding="utf8",
            ),
            logging.StreamHandler(),
        ],
    )
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="User Query", required=True)
    args = parser.parse_args()
    query = args.query
    startup()
    print(get_db_query(query))
    shutdown()

if __name__ == "__main__":
    main()