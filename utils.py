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
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationSummaryBufferMemory, ChatMessageHistory
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.vectorstores.redis import Redis
from langchain.callbacks import get_openai_callback
import redis
import uuid
from datetime import datetime, timezone
from langchain.prompts.few_shot import FewShotPromptTemplate
config = Config()

# sampleData = './data/SamplePDF.pdf'
# sampleDataTxt = './data/SampleTxt.txt'
# sampleData = './data/Apex Chat Sample Business Data.pdf'
sampleData = './data/Coffee.pdf'

# redisLocalHost = 'redis://localhost:6379'
redisLocalHost = 'redis://127.0.0.1:6379'

models = ['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4','gpt-4-32k']

sampleChatHistory =  [{'sender': 'user', 'message': 'What is my name'}, {'sender': 'AI', 'message': 'Your name is Innocent.'}]
# template = """
#     You are a Coffee business having a conversation with a client.
#     Given the following extracted parts of your business data and question, give a response.
#     {context}
#     {chat_history}
#     Human: {human_input}
#     Chatbot:"""
    
#prompt template    
# template = """
#     You are an AI assistant for a business that sells coffee paste. Given extracted context from business data and conversation history, provide support to any questions customers may have. Only provide information related to the business.
    
#     Here are some workflows to keep in mind
#     If the client wants to place an order get the following details; Name, Flavour, Quantity, Primary Contact, Secondary Contact, Delivery Address. 
    # If an order is placed with all the details provided respond only with a json of the order details with the keys name, flavour, quantity, contact1, contact2, address
#     If the client is confirming their order, respond only with the code ORDERCONFIRMATION and a json of the order details 
    
#     Previous Conversation: {chat_history}    
#     Business Information: {context}
#     Human: {human_input}
#     Chatbot:"""
    
# template = """
#     You are an AI assistant for a business specializing in coffee paste. Your primary goal is to provide support and assistance to customers based on extracted context from business data and conversation history. Focus on delivering accurate and relevant information related to the business. Do not generate answers that are not supported by the provided business context.
    
#     If the client expresses an intention to place an order, guide them to provide the following details: Name, Flavour, Quantity, Primary Contact, Secondary Contact, Delivery Address
    
#     If a recent order has been placed with all required details, your response should only strictly be a json with the order "name", "flavour", "quantity", "contact1", "contact2", "address"
    
#     Previous Conversation: {chat_history}    
#     Business Information: {context}
#     Human: {human_input}
#     Chatbot:"""




template = """
    You are an AI assistant for a business specializing in coffee paste. Your primary goal is to provide support and assistance to customers based on extracted context from business data and conversation history. Focus on delivering accurate and relevant information related to the business. Do not generate answers that are not supported by the provided business context.
    
    If the client expresses an intention to place an order, guide them to provide the following details: Name, Flavour, Quantity, Primary Contact, Secondary Contact, Delivery Address
    
   If a recent order has been placed with all required details, your response should begin with 0RD3R9LAC3D followed strictly by a JSON of "name", "flavour", "quantity", "contact1", "contact2", "address". Provide the information in the requested format.
    
    Previous Conversation: {chat_history}    
    Business Information: {context}
    Human: {human_input}
    Chatbot:"""
    
    
    # Example:
    # ORDERPLACED4564
    # name: Innocent,
    # flavour: Hazelnut,
    # quantity: 4,
    # contact1: 0557187667,
    # contact2: 5454636456,
    # address: Ghana

    
#prompt template
prompt = PromptTemplate(
        input_variables=["chat_history", "human_input", "context"],
        template=template
    )
embeddings = OpenAIEmbeddings(openai_api_key=config.OPENAI_API_KEY)

#use chain
def use_load_qa_chain(memory, prompt, query, docs):
    with get_openai_callback() as cb:
        # models
        models = ['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4','gpt-4-32k']
        model = models[0]
        #Please provide a valid OpenAI model name.Known models are: gpt-4, gpt-4-0314, gpt-4-completion, gpt-4-0314-completion, gpt-4-32k, gpt-4-32k-0314, gpt-4-32k-completion, gpt-4-32k-0314-completion, gpt-3.5-turbo, gpt-3.5-turbo-0301, text-ada-001, ada, text-babbage-001, babbage, text-curie-001, curie, text-davinci-003, text-davinci-002, code-davinci-002
        chain = load_qa_chain(ChatOpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model_name=config.MODEL), chain_type="stuff", memory=memory, prompt=prompt, verbose=False)
        # chain = load_qa_chain(OpenAI(temperature=0, openai_api_key=config.OPENAI_API_KEY, model_name=model), chain_type="stuff", memory=memory, prompt=prompt)
        chain_output = chain({"input_documents":docs, "human_input": query}, return_only_outputs=False)
        print ('conversation history', chain.memory.buffer)
        # print ('conversation memory', chain.memory)
        # Print the entire chain information
        # print('Chain information:', chain_output)
        save_to_summary(chain.memory.buffer, 'system', True)
        print('callback info', cb)
        # save_variable_to_file(chain.memory.buffer, 'summary.txt')        
        return chain_output['output_text']
    
def save_to_summary(msg, sender, summary_provided = False):
    return # remove to use summary
    if summary_provided:
        save_variable_to_file(msg, 'summary.txt')
    else:
        print('saving to summary.....')
        previous_summary = read_variable_from_file('summary.txt')
        print('previous summary', previous_summary)
        if not previous_summary:
            previous_summary = ""
        history = ChatMessageHistory()
        if sender == "system":
            history.add_ai_message(msg)
        elif sender == "human":
            history.add_user_message(msg)
        memory = ConversationSummaryMemory(
            llm=ChatOpenAI(temperature=0, model_name=config.MODEL),
            chat_memory=history,
            # buffer=previous_summary,
            return_messages = True,
        )
        new_summary = memory.predict_new_summary(memory.chat_memory.messages, previous_summary)
        print ('new summary', new_summary)
        save_variable_to_file(new_summary, 'summary.txt')
            

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


def ttl_expire(chatHistory):
    if len(chatHistory) == 0:
        return True
    time_string = chatHistory[-1]['created_time']
    parsed_time = datetime.strptime(time_string, '%Y-%m-%dT%H:%M:%S%z')
    parsed_time = parsed_time.replace(tzinfo=timezone.utc)
    print ('last message date', parsed_time)
    current_time = datetime.now(timezone.utc)
    print ('current date', current_time)
    time_difference = current_time - parsed_time
    hours_passed = time_difference.total_seconds() / 3600
    print ('hours passed', hours_passed)
    days_passed = time_difference.days
    print ('days passed', days_passed)
    if days_passed > 7:
        return True
    return False

def createConversationBufferMemory(chatHistory):
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="human_input")
    print ('utils ->', chatHistory)
    for chat in chatHistory:
        chat_message = chat['message']
        chat_sender = chat['sender']
        if chat_sender == 'human':
                memory.chat_memory.add_user_message(chat_message)
        else:
            memory.chat_memory.add_ai_message(chat_message)
            memory.chat_memory.messages
        # if chat_sender != 'system':     
        #     # if chat['sender'] == 'AI':
        #     #     memory.chat_memory.add_ai_message(chat_message)
        #     # else:
        #     #     memory.chat_memory.add_user_message(chat_message)
        #     if chat['sender'] == 'human':
        #         memory.chat_memory.add_user_message(chat_message)
        #     else:
        #         memory.chat_memory.add_ai_message(chat_message)
    return memory

def useConversationSummary(chatHistory):
    previous_summary = read_variable_from_file('summary.txt')
    if (ttl_expire(chatHistory) or not previous_summary): # or previous summary empty
    # if (False): # or previous summary empty
        # building memory
        history = ChatMessageHistory()
        for chat in chatHistory:
            if chat['sender'] == 'human':
                # memory.save_context({"input": chat['message']})
                history.add_user_message(chat['message'])
            else:
                # memory.save_context({"output": chat['message']})
                history.add_ai_message(chat['message'])
        memory = ConversationSummaryMemory(
            llm=ChatOpenAI(temperature=0, model_name=config.MODEL),
            chat_memory=history,
            return_messages = True,
        )
        # print ('memory buffer', memory.buffer)
        messages = memory.chat_memory.messages
        new_summary = memory.predict_new_summary(messages, "") 
        print ('new_summary', new_summary)
        new_memory = ConversationSummaryMemory(
        llm=ChatOpenAI(temperature=0, model_name=config.MODEL),
        buffer=new_summary,
        memory_key="chat_history", 
        input_key="human_input"
    )
        return new_memory
        # return 
        # return memory
    else:
        memory = ConversationSummaryMemory(
        llm=ChatOpenAI(temperature=0, model_name=config.MODEL),
        buffer=previous_summary,
        memory_key="chat_history", 
        input_key="human_input"
    )
        # return 
        return memory

def read_variable_from_file(filename):
    with open(filename, 'r') as file:
        content = file.read()
        return content.strip()
    
def save_variable_to_file(variable, filename):
    with open(filename, 'w') as file:
        file.write(str(variable))

def createMemoryChatHistory(chatHistory):
    return createConversationBufferMemory(chatHistory)
    # return useConversationSummary(chatHistory)
    

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
    try:
        persistent_path = 'persistent/' + indexKey
        if (os.path.exists(persistent_path)):    
            vectordb = Chroma(persist_directory=persistent_path, embedding_function=embeddings)
            docs = vectordb.similarity_search(query)
            memory = createMemoryChatHistory(chatHistory)
            return use_load_qa_chain(memory, prompt, query, docs)
        else:
            # print ('path does not exist')
            return 'path does not exist'
    except Exception as e:
        print ('queryIndexWithChromaFromPersistent exception', e)
        raise

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
    # print(queryIndexWithChromaFromPersistent(config.HARDCODED_INDEX_KEY,'I would want to place an order for coffee?',[]))
    createIndexWithChroma(sampleData)
    # pass