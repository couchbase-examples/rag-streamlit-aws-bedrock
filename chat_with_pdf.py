import tempfile
from langchain_community.vectorstores import CouchbaseVectorStore
from langchain_community.document_loaders import PyPDFLoader
import os
import streamlit as st
import boto3
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain.llms.bedrock import Bedrock 


def check_environment_variable(variable_name):
    """Check if environment variable is set"""
    if variable_name not in os.environ:
        st.error(
            f"{variable_name} environment variable is not set. Please add it to the secrets.toml file"
        )
        st.stop()


def save_to_vector_store(uploaded_file, vector_store):
    """Chunk the PDF & store it in Couchbase Vector Store"""
    if uploaded_file is not None:
        temp_dir = tempfile.TemporaryDirectory()
        temp_file_path = os.path.join(temp_dir.name, uploaded_file.name)

        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
            loader = PyPDFLoader(temp_file_path)
            docs = loader.load()

        vector_store.add_documents(docs)
        st.info(f"PDF loaded into vector store in {len(docs)} documents")


@st.cache_resource(show_spinner="Connecting to Vector Store")
def get_vector_store(
    _cluster,
    db_bucket,
    db_scope,
    db_collection,
    _embedding,
    index_name,
):
    """Return the Couchbase vector store"""
    vector_store = CouchbaseVectorStore(
        cluster=_cluster,
        bucket_name=db_bucket,
        scope_name=db_scope,
        collection_name=db_collection,
        embedding=_embedding,
        index_name=index_name,
    )
    return vector_store


@st.cache_resource(show_spinner="Connecting to Couchbase")
def connect_to_couchbase(connection_string, db_username, db_password):
    """Connect to couchbase"""
    from couchbase.cluster import Cluster
    from couchbase.auth import PasswordAuthenticator
    from couchbase.options import ClusterOptions
    from datetime import timedelta

    auth = PasswordAuthenticator(db_username, db_password)
    options = ClusterOptions(auth)
    connect_string = connection_string
    cluster = Cluster(connect_string, options)

    # Wait until the cluster is ready for use.
    cluster.wait_until_ready(timedelta(seconds=5))

    return cluster


if __name__ == "__main__":
    # # Authorization
    # if "auth" not in st.session_state:
    #     st.session_state.auth = False

    st.set_page_config(
        page_title="Chat with your PDF using Langchain, Couchbase & Gemini Pro",
        page_icon="🤖",
        layout="centered",
        initial_sidebar_state="auto",
        menu_items=None,
    )

    # AUTH = os.getenv("LOGIN_PASSWORD")
    # check_environment_variable("LOGIN_PASSWORD")

    # # Authentication
    # user_pwd = st.text_input("Enter password", type="password")
    # pwd_submit = st.button("Submit")

    # if pwd_submit and user_pwd == AUTH:
    #     st.session_state.auth = True
    # elif pwd_submit and user_pwd != AUTH:
    #     st.error("Incorrect password")

    # if st.session_state.auth:
    # Load environment variables
    DB_CONN_STR = os.getenv("DB_CONN_STR")
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_BUCKET = os.getenv("DB_BUCKET")
    DB_SCOPE = os.getenv("DB_SCOPE")
    DB_COLLECTION = os.getenv("DB_COLLECTION")
    INDEX_NAME = os.getenv("INDEX_NAME")

    # Ensure that all environment variables are set
    check_environment_variable("DB_CONN_STR")
    check_environment_variable("DB_USERNAME")
    check_environment_variable("DB_PASSWORD")
    check_environment_variable("DB_BUCKET")
    check_environment_variable("DB_SCOPE")
    check_environment_variable("DB_COLLECTION")
    check_environment_variable("INDEX_NAME")

    bedrock_client = boto3.client("bedrock-runtime", region_name="ap-south-1")
    # Use Gecko Embeddings
    embedding = BedrockEmbeddings(bedrock_client)

    # Connect to Couchbase Vector Store
    cluster = connect_to_couchbase(DB_CONN_STR, DB_USERNAME, DB_PASSWORD)

    vector_store = get_vector_store(
        cluster,
        DB_BUCKET,
        DB_SCOPE,
        DB_COLLECTION,
        embedding,
        INDEX_NAME,
    )

    # Use couchbase vector store as a retriever for RAG
    retriever = vector_store.as_retriever()

    # Build the prompt for the RAG
    template = """You are a helpful bot. If you cannot answer based on the context provided, respond with a generic answer. Answer the question as truthfully as possible using the context below:
    {context}

    Question: {question}"""

    prompt = ChatPromptTemplate.from_template(template)

    # Use Gemini Pro as the LLM for the RAG
    aws_model_id = "meta.llama3-8b-instruct-v1:0"
    llm = Bedrock(client=bedrock_client, model_id=aws_model_id)
    # RAG chain
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # # Pure Gemini output without RAG
    # template_without_rag = """You are a helpful bot. Answer the question as truthfully as possible.

    # Question: {question}"""

    # prompt_without_rag = ChatPromptTemplate.from_template(template_without_rag)

    # llm_without_rag = GoogleGenerativeAI(
    #     temperature=0,
    #     model="models/gemini-1.5-pro",
    # )

    # chain_without_rag = (
    #     {"question": RunnablePassthrough()}
    #     | prompt_without_rag
    #     | llm_without_rag
    #     | StrOutputParser()
    # )

    # Frontend
    couchbase_logo = (
        "https://emoji.slack-edge.com/T024FJS4M/couchbase/4a361e948b15ed91.png"
    )

    st.title("Chat with PDF")
    st.markdown(
        "Answers with [Couchbase logo](https://emoji.slack-edge.com/T024FJS4M/couchbase/4a361e948b15ed91.png) are generated using *RAG* while 🤖 are generated by pure *LLM (Gemini)*"
    )

    with st.sidebar:
        st.header("Upload your PDF")
        with st.form("upload pdf"):
            uploaded_file = st.file_uploader(
                "Choose a PDF.",
                help="The document will be deleted after one hour of inactivity (TTL).",
                type="pdf",
            )
            submitted = st.form_submit_button("Upload")
            if submitted:
                # store the PDF in the vector store after chunking
                save_to_vector_store(uploaded_file, vector_store)

        st.subheader("How does it work?")
        st.markdown(
            """
            For each question, you will get two answers: 
            * one using RAG ([Couchbase logo](https://emoji.slack-edge.com/T024FJS4M/couchbase/4a361e948b15ed91.png))
            * one using pure LLM - Gemini (🤖). 
            """
        )

        st.markdown(
            "For RAG, we are using [Langchain](https://langchain.com/), [Couchbase Vector Search](https://couchbase.com/) & [Gemini](https://gemini.google.com/). We fetch parts of the PDF relevant to the question using Vector search & add it as the context to the LLM. The LLM is instructed to answer based on the context from the Vector Store."
        )

        # View Code
        if st.checkbox("View Code"):
            st.write(
                "View the code here: [Github](https://github.com/couchbaselabs/rag-gemini-demo/blob/master/chat_with_pdf.py)"
            )

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": "Hi, I'm a chatbot who can chat with the PDF. How can I help you?",
                "avatar": "🤖",
            }
        )

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=message["avatar"]):
            st.markdown(message["content"])

    # React to user input
    if question := st.chat_input("Ask a question based on the PDF"):
        # Display user message in chat message container
        st.chat_message("user").markdown(question)

        # Add user message to chat history
        st.session_state.messages.append(
            {"role": "user", "content": question, "avatar": "👤"}
        )

        # Add placeholder for streaming the response
        with st.chat_message("assistant", avatar=couchbase_logo):
            message_placeholder = st.empty()

        # stream the response from the RAG
        rag_response = ""
        for chunk in chain.stream(question):
            rag_response += chunk
            message_placeholder.markdown(rag_response + "▌")

        message_placeholder.markdown(rag_response)
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": rag_response,
                "avatar": couchbase_logo,
            }
        )

        # # stream the response from the pure LLM

        # # Add placeholder for streaming the response
        # with st.chat_message("ai", avatar="🤖"):
        #     message_placeholder_pure_llm = st.empty()

        # pure_llm_response = ""

        # for chunk in chain_without_rag.stream(question):
        #     pure_llm_response += chunk
        #     message_placeholder_pure_llm.markdown(pure_llm_response + "▌")

        # message_placeholder_pure_llm.markdown(pure_llm_response)
        # st.session_state.messages.append(
        #     {
        #         "role": "assistant",
        #         "content": pure_llm_response,
        #         "avatar": "🤖",
        #     }
        # )
