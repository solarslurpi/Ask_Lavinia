from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    download_loader,
    ListIndex,
    TreeIndex,
)
from llama_index.callbacks import CallbackManager, TokenCountingHandler
import tiktoken
import faiss
from tqdm import tqdm
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import json
import sqlite3
from logging_handler import LoggingHandler
import logging
import streamlit as st
from sqlalchemy import text


def _setup_store() -> FaissVectorStore:
    # dimensions of text-ada-embedding-002
    d = 1536
    faiss_index = faiss.IndexFlatL2(d)
    store = FaissVectorStore(faiss_index=faiss_index)
    return StorageContext.from_defaults(vector_store=store)


def utils_ListStoreIndex_documents(docs):
    storage_context = _setup_store()
    index = ListIndex.from_documents(
        tqdm(docs, desc="Indexing documents"), storage_context=storage_context
    )
    return index


def utils_VectorStoreIndex_documents(docs):
    storage_context = _setup_store()
    index = VectorStoreIndex.from_documents(
        tqdm(docs, desc="Indexing documents"), storage_context=storage_context
    )
    return index


def utils_TreeStoreIndex_documents(docs):
    storage_context = _setup_store()
    index = TreeIndex.from_documents(
        tqdm(docs, desc="Indexing documents"), storage_context=storage_context
    )
    return index


def utils_store_index(index, name: str) -> None:
    index.storage_context.persist(persist_dir=name)


# @st.cache_resource
def utils_load_index(name: str):
    try:
        # load index from disk
        vector_store = FaissVectorStore.from_persist_dir(name)
        storage_context = StorageContext.from_defaults(
            persist_dir=name, vector_store=vector_store
        )
        index = load_index_from_storage(
            persist_dir=name, storage_context=storage_context
        )
        return index
    except Exception as e:
        print(f"ERROR: {e}. Exiting.")
        sys.exit(1)


def utils_get_urls(base_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    response = requests.get(base_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    urls = set()
    for link in soup.find_all("a"):
        href = link.get("href")
        if href:
            print(href)
            full_url = None
            if href.startswith("http") and base_url in href:
                full_url = href
            elif href.startswith("/") or href.startswith("#"):
                full_url = urljoin(base_url, href)
            # This one is for kirklandwa.gov web site.
            # Include only URLs that have 'oc_lang=en' or do not contain 'oc_lang=' at all
            if full_url and ("oc_lang=" not in full_url or "oc_lang=en" in full_url):
                urls.add(full_url)
    return urls


def utils_get_llama_documents(file_with_urls):
    with open(file_with_urls, "r") as file:
        urls = file.read().splitlines()
    # small group for testing...
    ## Use the WebBaseLoader to load the content from the URLs
    BeautifulSoupWebReader = download_loader("BeautifulSoupWebReader")
    loader = BeautifulSoupWebReader()
    llama_documents = loader.load_data(tqdm(urls))
    return llama_documents


def utils_get_audio_documents(audio_filename):
    AudioTranscriber = download_loader("AudioTranscriber")
    loader = AudioTranscriber()
    documents = loader.load_data(audio_filename)
    return documents


def utils_calculate_cost(model_name, num_prompt_tokens, num_completion_tokens) -> float:
    """Calculate the total cost for a specified model based on the number of prompt and completion tokens."""

    # Load data from JSON file
    with open("openai_costs.json") as f:
        data = json.load(f)

    try:
        costs = data["openai_LLMs"][model_name]
        prompt_cost = costs["prompt"]
        completion_cost = costs["completion"]

        # Calculate total cost
        total_cost = (prompt_cost * num_prompt_tokens) + (
            completion_cost * num_completion_tokens
        )
        return total_cost
    except KeyError:
        return "Model not found in data."


from tiktoken.model import MODEL_TO_ENCODING


# Now MODEL_TO_ENCODING is a dictionary where keys are model names and values are their encodings
# We can transform it into a list of dictionaries
def utils_get_llm_names_and_encoding() -> list:
    list_of_dicts = [{"model": k, "encoding": v} for k, v in MODEL_TO_ENCODING.items()]
    return list_of_dicts


def utils_store_qa(visible: bool, cost: float, question: str, response: str):
    # with open("qa_results.txt", "a") as f:
    #     f.write("-" * 50 + "\n")
    #     f.write(f"(Cost: ${cost})      Question: {question}\n ")
    #     f.write("-" * 50 + "\n")
    #     f.write(f"Response: {response}\n")
    # Added user feedback functionality
    logger = LoggingHandler(log_level=logging.DEBUG)
    # conn = sqlite3.connect(dbname)
    conn = st.experimental_connection("askl", type="sql")
    with conn.session as s:
        # Create the qa table if it does not exist.
        s.execute(
            text(
                """CREATE TABLE IF NOT EXISTS qa_table (
            questionID INTEGER PRIMARY KEY AUTOINCREMENT,
            visible BOOL,
            cost REAL, 
            question TEXT, 
            response TEXT
        )"""
            )
        )
        # Check to make sure table was created.
        res = s.execute(text("Select name FROM sqlite_master"))
        table_name = res.fetchone()[0]
        if table_name != "qa_table":
            raise Exception("ERROR: Table qa_table could not be created.")
        # Check if a row with the same question already exists
        res = s.execute(
            text(f"SELECT * FROM qa_table WHERE question LIKE '{question}'")
        )
        existing_row = res.fetchone()  # fetchone() returns None if no row is found

        # If no row with the same question exists, insert the new row
        if existing_row is None:
            s.execute(
                text(
                    """
                INSERT INTO qa_table (visible, cost, question, response)
                VALUES (:visible, :cost, :question, :response)
                """
                ),
                {
                    "visible": visible,
                    "cost": cost,
                    "question": question,
                    "response": response,
                },
            )

            # s.execute(text(
            #     """
            #     INSERT INTO qa_table (visible, cost, question, response)
            #     VALUES ( ?, ?, ?, ?)
            # """),
            #     (visible, cost, question, response),
            # )
            logger.DEBUG(f"Wrote row to the table {table_name}")
        else:
            logger.DEBUG(f"Row with {question} already exists in {table_name}")

        # Commit the changes
        s.commit()


class TokenCount:
    """
    A class to count up the number of tokens used.

    Attributes
    ----------
    token_counter : TokenCountingHandler
        a TokenCountingHandler object that counts tokens in the model
    callback_manager : CallbackManager
        a CallbackManager object that manages callbacks for the token counter

    """

    def __init__(self, model_name, verbose=True):
        """
        Initializes the TokenCost object.

        Parameters
        ----------
        model_name : str
            The name of the model to be token counted.  Common names are 'text-davinci-003'
        verbose : bool, optional
            Whether to print the token counting progress to the console. Default is True.
        """
        self._callback_manager = None

        # Set up callback
        # Note: If they generate an error, an upper level try/except will catch.
        self.token_counter = TokenCountingHandler(
            tokenizer=tiktoken.encoding_for_model(model_name).encode, verbose=verbose
        )

        self.callback_manager = CallbackManager([self.token_counter])

    @property
    def callback_manager(self):
        return self._callback_manager

    @callback_manager.setter
    def callback_manager(self, value):
        self._callback_manager = value

    @property
    def embedding_token_count(self):
        return self.token_counter.embedding_token_counts

    @property
    def prompt_token_count(self):
        return self.token_counter.prompt_llm_token_count

    @property
    def completion_token_count(self):
        return self.token_counter.completion_llm_token_count

    @property
    def total_token_count(self):
        return self.token_counter.total_llm_token_count

    @property
    def prompt(self):
        return self.token_counter.llm_token_counts[-1].prompt

    @property
    def completion(self):
        return self.token_counter.llm_token_counts[-1].completion
