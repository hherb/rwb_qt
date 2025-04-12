from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.models.ollama import Ollama
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb

# Define the database URL where the vector database will be stored
db_url = "/tmp/lancedb"

#MODEL = "granite3.2:8b-instruct-q8_0"  # Model ID for Ollama
MODEL="qwen2.5:14b-instruct-q8_0"
#MODEL="qwen2.5:32b-instruct-q8_0"
#MODEL="llama3.1:8b-instruct-q8_0"
# Configure the language model
model = Ollama(id=MODEL)

# Create Ollama embedder
embedder = OllamaEmbedder(id="nomic-embed-text", dimensions=768)

# Create the vector database
vector_db = LanceDb(
    table_name="recipes",  # Table name in the vector database
    uri=db_url,  # Location to initiate/create the vector database
    embedder=embedder,  # Without using this, it will use OpenAIChat embeddings by default
)

# Create a knowledge base from a PDF URL using LanceDb for vector storage and OllamaEmbedder for embedding
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

# Load the knowledge base without recreating it if it already exists in Vector LanceDB
knowledge_base.load(recreate=False)

# Set up SQL storage for the agent's data
storage = SqliteStorage(table_name="recipes", db_file="data.db")
storage.create()  # Create the storage if it doesn't exist

# Initialize the Agent with various configurations including the knowledge base and storage
agent = Agent(
    session_id="session_id",  # use any unique identifier to identify the run
    user_id="user",  # user identifier to identify the user
    model=model,
    knowledge=knowledge_base,
    storage=storage,
    show_tool_calls=True,
    debug_mode=True,  # Enable debug mode for additional information
)

# Use the agent to generate and print a response to a query, formatted in Markdown
agent.print_response(
    "What is the first step of making Gluai Buat Chi from the knowledge base?",
    markdown=True,
)