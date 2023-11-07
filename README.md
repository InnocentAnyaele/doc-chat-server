# doc-chat-server

![Screenshot_20230727-160244](https://github.com/InnocentAnyaele/doc-chat-server/assets/55434969/87eae2e3-aff9-4266-99dd-77f3acdf9fc9)

**About the project**

Think about a business whose data can be fed into ChatGPT's LLM so that their chatbot can fully engage clients' queries and concerns through instagram message.

This project creates a vector storage of dummy business data using Langchain & Chroma DB (also has support for Redis and Pinecone) so that they can be queried with OpenAI’s LLM to return a response. It converts the data into text chunks which as stored on the disk as vectors (using Chroma db)

See Langchain & Chroma db documentation here 

[Chroma — 🦜🔗 LangChain 0.0.157](https://python.langchain.com/en/latest/modules/indexes/vectorstores/examples/chroma.html)

When a customer messages the business' Instagram page

1. A webhook is sent to the Flask server

2. The message is received and Chroma db performs a 'vector cosine similarity search' across the stored vectors to return data about the business that is relevant to the client's query.

3. It then takes this 'context' data, the chat history of Apex and the Client, and the customers question and feeds all this into OpenAI's language model to return a response

4. The response is sent to the user.

**Setting Up**



* Clone the project
* Get all the necessary keys for the config file
* Use any of the ‘creating index’ functions in the utils.py file to create your business data (chroma, redis, pinecone). Just set your location to your data file (pdf format) in the utils.py file

    Note that these functions will return an index name / key that will be required when you want to query this index. 


    We use Chroma so we can add it to our config file as HARDCODED_INDEX_KEY

* You can also edit the prompt template to include the prompt
* When all the files are set, run the flask server to listen for webhooks and generate the response.

This project uses Meta developer API so some setup there is required to get some of the keys such as user access token, page access token, user_id, page_id, etc. See their docs for setting up Instagram messaging. 

[Instagram Messaging - Messenger Platform - Documentation - Meta for Developers (facebook.com)](https://developers.facebook.com/docs/messenger-platform/instagram/)

The code in the fb.py contains the functions that handle anything to do with Meta such as 



* Getting a list of all messages from an Instagram user
* Finding conversations with a specific user 
* Sending the user a message

It also contains other meta functions that aren’t actively used in the project but are there for doing some tests during development.

The code in utils.py contains functions for creating the vectors for business data, getting relevant vectors when we do a cosine similarity search, querying those vectors with open AI LLM etc. 

It also contains other functions that aren’t actively used in the project but are there for doing some tests during development.

The app.py contains the webhook route along with two other api; addData and queryIndex,



* You can use the addData api to send your pdf file via a post request to create the index. The form data includes the files and a fileLength (how many files sent) variable.
* You can use the queryIndex to manually query the created index. This takes in an array of the chatHistory, the query and the index name. 

When all the config keys are set, you can start the flask server [flask run]

**Contributing**

I welcome contributions from anyone! To contribute to this project, follow these steps:



* Fork the repository to your own GitHub account.
* Clone the forked repository to your local machine.
* Create a new branch for your changes with a descriptive name (e.g., fix-bug-123).
* Make your changes to the codebase.
* Commit your changes with a clear and descriptive commit message.
* Push your changes to your forked repository.
* Create a pull request (PR) from your forked repository to the original repository's master branch.
* Describe your changes in the PR description and link to any relevant issues or pull requests.
* Wait for feedback.

Thank you for your interest in contributing to this project!

 
