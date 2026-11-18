## RAG Demo using Couchbase, Streamlit, Langchain, and Amazon Bedrock

This is a demo app built to chat with your custom PDFs using the vector search capabilities of Couchbase to augment the Amazon Bedrock LLM results in a Retrieval-Augmented-Generation (RAG) model.

### How does it work?

You can upload your PDFs with custom data & ask questions about the data in the chat box.

For each question, you will get two answers:

- one using RAG (Couchbase logo)
- one using pure LLM - Amazon Titan on Bedrock (🤖).

For RAG, we are using Langchain, Couchbase Vector Search & Amazon Bedrock. We fetch parts of the PDF relevant to the question using Vector search & add it as the context to the LLM. The LLM is instructed to answer based on the context from the Vector Store.

### How to Run

- #### Install dependencies

  `pip install -r requirements.txt`

- #### Set the environment secrets

  Copy the `secrets.example.toml` file in the `.streamlit` folder, rename it to `secrets.toml`, and replace the placeholders with the actual values for your environment. AWS credentials are picked up by `boto3` from the usual places (environment variables, `~/.aws/credentials`, or an IAM role).

  ```
  DB_CONN_STR = "<connection_string_for_couchbase_cluster>"
  DB_USERNAME = "<username_for_couchbase_cluster>"
  DB_PASSWORD = "<password_for_couchbase_cluster>"
  DB_BUCKET = "<name_of_bucket_to_store_documents>"
  DB_SCOPE = "<name_of_scope_to_store_documents>"
  DB_COLLECTION = "<name_of_collection_to_store_documents>"
  INDEX_NAME = "<name_of_fts_index_with_vector_support>"

  # Optional Bedrock settings (defaults shown)
  AWS_REGION = "us-east-1"
  BEDROCK_EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"
  BEDROCK_LLM_MODEL = "amazon.titan-text-express-v1"
  ```

  The models must be enabled for your AWS account in the chosen region. If you change `BEDROCK_EMBEDDING_MODEL`, update the vector `dims` in the index definition to match the new model's output size.

- #### Create the Search Index on Full Text Service

  We need to create the Search Index on the Full Text Service in Couchbase. For this demo, you can import the index definition in [`index_definition.json`](index_definition.json).

  - [Couchbase Capella](https://docs.couchbase.com/cloud/search/import-search-index.html)

    - Import `index_definition.json` in Capella using the instructions in the documentation.
    - Click on Create Index to create the index.

  - [Couchbase Server](https://docs.couchbase.com/server/current/search/import-search-index.html)

    - Click on Search -> Add Index -> Import
    - Paste the contents of `index_definition.json` in the Import screen
    - Click on Create Index to create the index.

  #### Index Definition

  `index_definition.json` creates the index `pdf_search` on the documents in the `_default` collection within the `_default` scope in the bucket `awsbedrock`. The Vector field is set to `embedding` with 1024 dimensions (the output size of Amazon Titan Text Embeddings V2) and the text field set to `text`. We are also indexing and storing all the fields under `metadata` in the document as a dynamic mapping to account for varying document structures. The similarity metric is set to `dot_product`. If you use a different bucket, scope, collection, or embedding model, edit the bucket name (`sourceName`), the type mapping key (`<scope>.<collection>`), and `dims` before importing.

- #### Run the application

  `streamlit run chat_with_pdf.py`

