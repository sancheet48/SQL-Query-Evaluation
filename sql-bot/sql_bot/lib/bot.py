"""Query Bot Module."""
import argparse
from logging.handlers import RotatingFileHandler
import logging
import os
import sys
from time import time
import chromadb
from chromadb.config import Settings
from fastapi.responses import JSONResponse
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import const
from sql_bot.lib.output_modifier import SQLProcessor
from sql_bot.lib.llm_models import LLM_MODEL
from sql_bot.vector_db.vector_db_models import EMBEDDING_FUNCTION
import warnings

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class QueryBot:
    LLM_TEMPLATE = (
        "### System: \n You are a helpful assistant to convert text to "
        + "SQL query. Answer exactly in one line from the schema. "
        + "Generate a single SQL query for the question from schema below : "
        + "{schema} "
        + "\n### User: \n{question}"
        + "\n### Assistant:\n "
    )

    def __init__(self):
        self.llm_schema = ""
        self.chat_collection = None
        self.llm_prompt = PromptTemplate(
            template=self.LLM_TEMPLATE, input_variables=["question", "schema"]
        )
        self.llm_chain = LLMChain(prompt=self.llm_prompt, llm=LLM_MODEL)


    def startup(self):
        """
        Performs startup tasks, including loading the LLM schema and initializing the vector database.
        """

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
            self.llm_schema = file_p.read()

        if const.CHROMA_DB_PATH:
            if not os.path.isdir(const.CHROMA_DB_PATH):
                logger.error("'%s' directory not found", const.CHROMA_DB_PATH)
                sys.exit(-1)

            chroma_client = chromadb.PersistentClient(
                path=const.CHROMA_DB_PATH,
                settings=Settings(allow_reset=True, anonymized_telemetry=False),
            )
            self.chat_collection = chroma_client.get_collection(
                name="chat_collection", embedding_function=EMBEDDING_FUNCTION
            )

    def shutdown(self):
        """
        Shuts down the QueryBot instance, releasing any resources or connections.
        """
        pass

    def setup_logging():
        """
        Sets up logging to write messages to a rotating log file 'bot.log' and the console.
        Log format includes timestamp, level, module, line number, and message.
        """
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
    def retrieve_vdb(self, query: str) -> tuple:
        """
        Retrieves information from the vector database based on the given query.

        Args:
            query: The user's query string.

        Returns:
            A tuple containing:
                - A formatted string of results (questions and their corresponding SQL queries).
                - A list of similarity scores for each result.
        """
        if not self.chat_collection:
            return "", []
        query_result = self.chat_collection.query(query_texts=query, n_results=4)

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
            similarity_scores.append(1 - distance)

        output_string = output_string.rstrip(",\n")
        return output_string, similarity_scores

    def model_output(self, input_question: str, examples: str, similarity_scores: list) -> dict:
        """
        Generates a response using the LLM chain based on the input question and examples.

        Args:
            input_question: The user's query.
            examples: Relevant examples or context.
            similarity_scores: Similarity scores of retrieved examples.

        Returns:
            A dictionary containing the model's response, time taken, and similarity scores.
        """
        logging.info("User query: '%s'", input_question)
        start_time = time()
        response = self.llm_chain.run(
            {"question": input_question, "schema": self.llm_schema + examples}
        )
        time_taken = time() - start_time
        logging.info("LLM response: '%s'", response)
        api_response = self.get_api_response_template()
        api_response["model_response"] = response
        api_response["time_taken"] = time_taken
        api_response["similarity_scores"] = similarity_scores
        return api_response


    def get_api_response_template(self) -> dict:
        """
        Returns a template dictionary for structuring API responses.

        Returns:
            A dictionary with keys for model response, syntax validity, time taken, examples, and similarity scores.
        """
        return {
            "model_response": "",
            "is_valid_syntax": False,
            "time_taken": 0,
            "examples": "",
            "similarity_scores": [],
        }

    def sql_connect(self, api_response: dict) -> dict:
        """
        Processes the model response, likely parsing and validating SQL queries.

        Args:
            api_response: The API response dictionary.

        Returns:
            The updated API response dictionary with processed model response and syntax validity.
        """
        api_response["model_response"] = SQLProcessor.query_parser(api_response["model_response"])
        api_response["model_response"] = SQLProcessor.add_case_insensetiveness(api_response["model_response"])
        api_response["is_valid_syntax"] = SQLProcessor.validate_sql(api_response["model_response"])
        return api_response

    def get_db_query(self, query: str) -> JSONResponse:
        """
        Handles the complete query processing flow, from retrieval to SQL execution.

        Args:
            query: The user's query string

        Returns
            A JSONResponse containing the API response (model output, syntax validity, etc.)
        """
        examples, similarity_scores = self.retrieve_vdb(query)
        api_response = self.model_output(query, examples, similarity_scores)
        api_response["examples"] = examples
        try:
            api_response = self.sql_connect(api_response)
        except Exception as expt:
            logger.error("Exception: %s", expt)
            return JSONResponse(content=api_response, status_code=400)
        return JSONResponse(content=api_response, status_code=200)
    


def main():
    bot = QueryBot()
    bot.setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, help="User Query", required=True)
    args = parser.parse_args()
    query = args.query

    bot.startup()
    print(bot.get_db_query(query))
    bot.shutdown()

if __name__ == "__main__":
    main()