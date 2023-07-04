from llama_index import SimpleDirectoryReader
from myutils import (
    utils_VectorStoreIndex_documents,
    utils_store_index,
    utils_ListStoreIndex_documents,
    utils_TreeStoreIndex_documents,
)

print("Loading docs...")
docs = SimpleDirectoryReader("docs").load_data()
print("Making tree index...")
tree_index = utils_TreeStoreIndex_documents(docs)
print("Storing tree index...")
utils_store_index(tree_index, "indices/tree_index")
print("Making vector index...")
vector_index = utils_VectorStoreIndex_documents(docs)
print("Storing vector index...")
utils_store_index(vector_index, "indices/vector_index")
print("Making list index...")
list_index = utils_ListStoreIndex_documents(docs)
print("Storing list index...")
utils_store_index(vector_index, "indices/list_index")
