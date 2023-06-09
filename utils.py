import time
import os
import shutil
import threading
from config import Config
import json

from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
from langchain.vectorstores import Pinecone
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from langchain.vectorstores.redis import Redis


import redis

import uuid
config = Config()

# sampleData = './data/SamplePDF.pdf'
sampleDataTxt = './data/SampleTxt.txt'
sampleData = './data/Apex Chat Sample Business Data.pdf'

# redisLocalHost = 'redis://localhost:6379'
redisLocalHost = 'redis://127.0.0.1:6379'

sampleChatHistory =  [{'sender': 'user', 'message': 'What is my name'}, {'sender': 'AI', 'message': 'Your name is Innocent.'}]
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
embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)


def createChunkFromPdf(path):
    loader = UnstructuredPDFLoader(path)
    data = loader.load()
    # print (f'You have {len(data)} document(s) in your data')
    # print (f'You have {len(data[0].page_content)} characters in your document')
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    # text_splitter = CharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    texts = text_splitter.split_documents(data)
    # print (f'Now you have {len(texts)} documents')
    # print (texts)
    return texts

def createChunkFromTxt(path):
    with open(path) as f:
        data = f.read()
    text_splitter = CharacterTextSplitter(chunk_size=50, chunk_overlap=0)
    texts = text_splitter.split_text(data)
    # print (texts)
    return texts


def createMemoryChatHistory(chatHistory):
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
    for chat in chatHistory:
        chat_message = chat['message']
        chat_sender = chat['sender']
        if chat_sender != 'system':     
            if chat['sender'] == 'AI':
                memory.chat_memory.add_ai_message(chat_message)
            else:
                memory.chat_memory.add_user_message(chat_message)
    return memory


def use_load_qa_chain(memory, prompt, query, docs):
    chain = load_qa_chain(OpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY), chain_type="stuff", memory=memory, prompt=prompt)
    chain_output = chain({"input_documents":docs, "human_input": query })
    # print ('conversation history', chain.memory.buffer)
    # print (chain_output['output_text'])
    return chain_output['output_text']

# PINECONE

def createIndex(path):
    texts = createChunkFromPdf(path)    
    api_key = config.PINECONE_API_KEY,
    pinecone.init(
    environment = 'us-west1-gcp-free')
    newIndexName = str(uuid.uuid1())
    pinecone.create_index(newIndexName, dimension=1536, metric='cosine')
    Pinecone.from_texts([t.page_content for t in texts], embeddings, index_name=newIndexName)
    # print (newIndexName)
    return newIndexName

def queryPineconeIndex(chatHistory, query, indexKey):
    memory = createMemoryChatHistory(chatHistory)
    pinecone.init(
    api_key = config.PINECONE_API_KEY,
    environment = 'us-west1-gcp-free')
    index = Pinecone.from_existing_index(index_name=indexKey, embedding=embeddings)
    docs = index.similarity_search(query, include_metadata = True)
    return use_load_qa_chain(memory, prompt, query, docs)


# REDDIS

def createIndexFromRedis(path):
    texts = createChunkFromPdf(path)
    index_name = str(uuid.uuid1())
    rds = Redis.from_documents(texts, embeddings, redis_url = redisLocalHost, index_name=index_name)
    # rds.index_name
    # print (index_name)
    return index_name

def queryRedisIndex(indexName, query, chatHistory):
    try:
        rds = Redis.from_existing_index(embeddings, redis_url=redisLocalHost, index_name=indexName)
        results = rds.similarity_search(query)
        memory = createMemoryChatHistory(chatHistory)
        return use_load_qa_chain(memory, prompt, query, results)
    except Exception as e:
        # print (e)
        # print ('Index name does not exist')
        return (e)
    
    # retriever = rds.as_retriever()
    # docs = retriever.get_relevant_documents(query)
    # retriever = rds.as_retriever(search_type="similarity_limit")
    # retriever.get_relevant_documents("where did ankush go to college?")
    


# CHROMA 

def createIndexWithChroma(path):
    texts = createChunkFromPdf(path)
    new_index = str(uuid.uuid1())
    persistent_directory = 'persistent/' + new_index
    vectordb = Chroma.from_documents(documents=texts, embedding=embeddings, persist_directory=persistent_directory)
    vectordb.persist()
    vectordb = None
    # print (new_index)
    return new_index

def queryIndexWithChromaFromPersistent(indexKey, query, chatHistory):
    persistent_path = 'persistent/' + indexKey
    if (os.path.exists(persistent_path)):    
        vectordb = Chroma(persist_directory=persistent_path, embedding_function=embeddings)
        docs = vectordb.similarity_search(query)
        memory = createMemoryChatHistory(chatHistory)
        return use_load_qa_chain(memory, prompt, query, docs)
    else:
        # print ('path does not exist')
        return 'path does not exist'

def queryIndexWithChroma(path, query, chatHistory):
    texts = createChunkFromPdf(path)
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(texts, embeddings)
    docs = docsearch.similarity_search(query)
    memory = createMemoryChatHistory(chatHistory)
    return use_load_qa_chain(memory, prompt, query, docs)
    




def delete_context(dirName):
    time.sleep(300)
    if os.path.exists(dirName):
        shutil.rmtree(dirName)
    else:
        return ('Path does not exist')
        
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
    # queryIndexWithChromaFromPersistent(config.HARDCODED_INDEX_KEY,'What is the document about?',[])
    # createIndexWithChroma(sampleData)
    pass