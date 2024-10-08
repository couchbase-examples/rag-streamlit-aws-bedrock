## RAG Demo using Couchbase, Streamlit, Langchain, and Gemini Pro

This is a demo app built to chat with your custom PDFs using the vector search capabilities of Couchbase to augment the Gemini Pro results in a Retrieval-Augmented-Generation (RAG) model.

### How does it work?

You can upload your PDFs with custom data & ask questions about the data in the chat box.

For each question, you will get two answers:

- one using RAG (Couchbase logo)
- one using pure LLM - Gemini Pro (🤖).

For RAG, we are using Langchain, Couchbase Vector Search & Gemini Pro. We fetch parts of the PDF relevant to the question using Vector search & add it as the context to the LLM. The LLM is instructed to answer based on the context from the Vector Store.

### How to Run

- #### Install dependencies

  `pip install -r requirements.txt`

- #### Set the environment secrets

  Copy the `secrets.example.toml` file in `.streamlit` folder and rename it to `secrets.toml` and replace the placeholders with the actual values for your environment

  ```
  GOOGLE_API_KEY = "<google_api_key>"
  DB_CONN_STR = "<connection_string_for_couchbase_cluster>"
  DB_USERNAME = "<username_for_couchbase_cluster>"
  DB_PASSWORD = "<password_for_couchbase_cluster>"
  DB_BUCKET = "<name_of_bucket_to_store_documents>"
  DB_SCOPE = "<name_of_scope_to_store_documents>"
  DB_COLLECTION = "<name_of_collection_to_store_documents>"
  INDEX_NAME = "<name_of_fts_index_with_vector_support>"
  LOGIN_PASSWORD = "<password to access the streamlit app>"
  ```

- #### Create the Search Index on Full Text Service

  We need to create the Search Index on the Full Text Service in Couchbase. For this demo, you can import the following index using the instructions.

  - [Couchbase Capella](https://docs.couchbase.com/cloud/search/import-search-index.html)

    - Copy the index definition to a new file index.json
    - Import the file in Capella using the instructions in the documentation.
    - Click on Create Index to create the index.

  - [Couchbase Server](https://docs.couchbase.com/server/current/search/import-search-index.html)

    - Click on Search -> Add Index -> Import
    - Copy the following Index definition in the Import screen
    - Click on Create Index to create the index.

  #### Index Definition

  Here, we are creating the index `pdf_search` on the documents in the `docs` collection within the `shared` scope in the bucket `pdf-docs`. The Vector field is set to `embeddings` with 768 dimensions and the text field set to `text`. We are also indexing and storing all the fields under `metadata` in the document as a dynamic mapping to account for varying document structures. The similarity metric is set to `dot_product`. If there is a change in these parameters, please adapt the index accordingly.

  ```
  {
    "name": "pdf_search",
    "type": "fulltext-index",
    "params": {
        "doc_config": {
            "docid_prefix_delim": "",
            "docid_regexp": "",
            "mode": "scope.collection.type_field",
            "type_field": "type"
        },
        "mapping": {
            "default_analyzer": "standard",
            "default_datetime_parser": "dateTimeOptional",
            "default_field": "_all",
            "default_mapping": {
                "dynamic": true,
                "enabled": false
            },
            "default_type": "_default",
            "docvalues_dynamic": false,
            "index_dynamic": true,
            "store_dynamic": false,
            "type_field": "_type",
            "types": {
                "shared.docs": {
                    "dynamic": true,
                    "enabled": true,
                    "properties": {
                        "embedding": {
                            "enabled": true,
                            "dynamic": false,
                            "fields": [
                                {
                                    "dims": 768,
                                    "index": true,
                                    "name": "embedding",
                                    "similarity": "dot_product",
                                    "type": "vector",
                                    "vector_index_optimized_for": "recall"
                                }
                            ]
                        },
                        "text": {
                            "enabled": true,
                            "dynamic": false,
                            "fields": [
                                {
                                    "index": true,
                                    "name": "text",
                                    "store": true,
                                    "type": "text"
                                }
                            ]
                        }
                    }
                }
            }
        },
        "store": {
            "indexType": "scorch",
            "segmentVersion": 16
        }
    },
    "sourceType": "gocbcore",
    "sourceName": "pdf-docs",
    "sourceParams": {},
    "planParams": {
        "maxPartitionsPerPIndex": 64,
        "indexPartitions": 16,
        "numReplicas": 0
    }
  }
  ```

- #### Run the application

  `streamlit run chat_with_pdf.py`


Ensure Line 25 is based on whatever scope & collection that i created. in this case, _default _default.

Ensure line 35, is based on 1024 dimensions for AWS Titan

Ensure that line 65 has the bucket name stated, in my case, awsbedrock is the bucket name

Ensure that i am using Titan Text Embeddings V2, amazon.titan-embed-text-v2:0 <- Model Name on line 124

Ensure that i am using US-East-1 on line 122

Ensure that i use Titan Text G1 as its LLM, model name is amazon.titan-text-express-v1 on Line 150

Line 167 - Ensure that the correct LLM models are used, in our case, AWS -  Bedrock(client=bedrock_client, model_id=aws_model_id)