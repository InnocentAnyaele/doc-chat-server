import time
import os
import shutil
import threading
from config import Config
import json

from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI


import uuid


config = Config()

sampleData = './data/SamplePDF.pdf'

sampleChatHistory =  [{'sender': 'system', 'message': 'Reading your document...'}, {'sender': 'system', 'message': 'Context has been uploaded. Ask away!! NB: Session will expire after 5 mins.'}, {'sender': 'user', 'message': 'test query'}, {'sender': 'AI', 'message': 'Sorry something went wrong. Try again later or restart context'}, {'sender': 'user', 'message': 'test'}, {'sender': 'system', 'message': 'Sorry something went wrong. Try again later or restart context'}, {'sender': 'system', 'message': 'Context has been cleared'}, {'sender': 'system', 'message': 'Reading your document...'}, {'sender': 'system', 'message': 'Context has been uploaded. Ask away!! NB: Session will expire after 5 mins.'}, {'sender': 'user', 'message': 'test'}, {'sender': 'AI', 'message': 'done'}, {'sender': 'user', 'message': 'test'}, {'sender': 'AI', 'message': 'done'}]



def createIndex(path):
    loader = UnstructuredPDFLoader(path)
    data = loader.load()
    
    # print (f'You have {len(data)} document(s) in your data')
    # print (f'You have {len(data[0].page_content)} characters in your document')
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    texts = text_splitter.split_documents(data)
    
    # print (f'Now you have {len(texts)} documents')
    
    embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
    
    pinecone.init(
    api_key = config.PINECONE_API_KEY,
    environment = 'us-west1-gcp-free')
    
    
    newIndexName = str(uuid.uuid1())
    pinecone.create_index(newIndexName, dimension=1536, metric='cosine')
    
    Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=newIndexName)
    
    print (newIndexName)
    return newIndexName

def queryPineconeIndex(chatHistory, query, indexKey):
    template = """
    You are a chatbot having a conversation with a human.

    Given the following extracted parts of a long document and a question, create a final answer.

    {context}

    {chat_history}
    Human: {human_input}
    Chatbot:"""

    prompt = PromptTemplate(
        input_variables=["chat_history", "human_input", "context"],
        template=template
    )

    memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
    
    embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)
    
    pinecone.init(
    api_key = config.PINECONE_API_KEY,
    environment = 'us-west1-gcp-free')
    
    index = Pinecone.from_existing_index(index_name=indexKey, embedding=embeddings)
    

    for chat in chatHistory:
        chat_message = chat['message']
        chat_sender = chat['sender']
        if chat_sender != 'system':     
            if chat['sender'] == 'AI':
                memory.chat_memory.add_ai_message(chat_message)
            else:
                memory.chat_memory.add_user_message(chat_message)
        
        
    # memory.save_context({"human_input": "What is my name"}, {"output": "Your name is Innocent"})
    # memory.save_context({"human_input": "How old am I"}, {"output": "I am 20 years old"})

    chain = load_qa_chain(OpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY), chain_type="stuff", memory=memory, prompt=prompt)
    docs = index.similarity_search(query, include_metadata = True)
    # chain_output = chain({"input_documents":docs, "human_input":query}, return_only_outputs=True)
    chain_output = chain({"input_documents":docs, "human_input":query})
    
    # print (chain_output)
    # print (type(chain_output))
    print ('conversation history', chain.memory.buffer)
    print (chain_output['output_text'])
    return chain_output['output_text']

def delete_context(dirName):
    time.sleep(300)
    if os.path.exists(dirName):
        shutil.rmtree(dirName)
    else:
        print('Path does not exist')
        
    return 'completed'

def startDeleteThread(dirName):
    t = threading.Thread(target=delete_context, args=(dirName,))
    t.start()    

def checkExtension(fileName):
    fileName_split = fileName.split('.') 
    fileExtension = fileName_split[-1]
    return fileExtension

def deleteAllData():
    path = './data/'
    if os.path.exists(path):
        shutil.rmtree(path)


if __name__ == '__main__':
    # createIndex(sampleData)
    # queryPineconeIndex(sampleChatHistory,'What is this document about?','a8ebbf9e-e8d7-11ed-83ea-20c19bff2da4')
    pass