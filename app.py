from flask import Flask, request, make_response
from config import DevelopmentConfig
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
from utils import createIndex, checkExtension, startDeleteThread, queryPineconeIndex, queryIndexWithChromaFromPersistent, save_to_summary
from fb import findConversationWithASpecificUser, getListOfAllMessageTextInConversation, sendCustomerAMessage, getListOfAllMessagesInConversation
from flask_cors import CORS
import json
# import random
# import re
from webhook import quick_reply, validate_order, process_response
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory, ConversationSummaryBufferMemory, ChatMessageHistory
from langchain.chat_models import ChatOpenAI
models = ['gpt-3.5-turbo','gpt-3.5-turbo-16k','gpt-4','gpt-4-32k']

def create_app(config = DevelopmentConfig()):
    
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(config)
        
    def token_required(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            token = request.headers['Authorization']
            if not token:
                response = make_response('Authorization is required')
                response.status_code = 500
                return response
            
            if app.config['BEARER_TOKEN'] != token:
                response = make_response('Invalid Token')
                response.status_code = 500
                return response
            
            return func(*args, **kwargs)
        
        return decorated_function

    @app.route('/')
    def index():
        # print ('hello world')
        return "Hello, World"


    @app.route('/api/addData', methods=['POST'])
    @token_required
    def add_data():
        if request.method == 'POST':
            # response = make_response('testIndexKey')
            # response.status_code = 200 
            # return response
            
            try:
                uniqueDirectoryName = str(uuid.uuid1())
                uniqueDirName = os.path.join('./data/', uniqueDirectoryName)
                os.makedirs(uniqueDirName)
                fileNamesArray = []
                for i in range(int(request.form['fileLength'])):
                    currFile = request.files['file'+str(i)]
                    currFileName = secure_filename(currFile.filename)
                    save_file_to_dir = os.path.join(uniqueDirName,currFileName)
                    fileNamesArray.append(currFileName)
                    currFile.save(save_file_to_dir)
                    
                startDeleteThread(uniqueDirName)
                
                extension = checkExtension(fileNamesArray[-1]) 
                
                if extension == 'pdf':
                    path_to_pdf = os.path.join(uniqueDirName,fileNamesArray[-1])
                    indexKey = createIndex(path_to_pdf)
                    response = make_response(indexKey)
                    response.status_code = 200
                    # print (indexKey)
                    return response
                else:
                    response = make_response(extension , 'is not accepted')
                    response.status_code = 400
                    # print (extension, 'is not accepted')
                    return (response)
            except Exception as e:
                # print (e)
                response = make_response('Something went wrong')
                response.status_code = 500
                return response
            
            
    @app.route('/api/queryIndex', methods=['POST'])
    @token_required
    def queryIndex():
        if request.method == 'POST':
            try:
                # indexKey = request.form['indexKey']
                indexKey = 'a8ebbf9e-e8d7-11ed-83ea-20c19bff2da4'
                query = request.form['prompt']
                chatHistory = json.loads(request.form['chatHistory'])
                
                
                # print ('this is the index key',indexKey)
                # print ('this is the chat history',chatHistory)
                # print (chatHistory[0])
                # print (chatHistory[0]['sender'])
                # print (chatHistory[0]['message'])
                
                output = queryPineconeIndex(chatHistory,query,indexKey)
                
                response = make_response(output)
                response.status_code = 200
                # print (output)
                return response
                
            except Exception as e:
                # print (e)
                response = make_response('Something went wrong')
                response.status_code = 500
                return response
                
        
    @app.route('/webhook/messaging-webhook', methods=['GET','POST'])
    def messagingWebhook():
        if request.method == 'GET':
            mode = request.args.get('hub.mode')
            token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')

            if mode and token:
                if mode == 'subscribe' and token == app.config['VERIFY_TOKEN']:
                    # print('WEBHOOK_VERIFIED')
                    return make_response(challenge,200)
                else:
                    return make_response('',403)
            else:
                # print ('Got webhook but without parameters')
                return
        if request.method == 'POST':
            body = request.get_json()
            entry = body['entry']
            
            try:
                if body['object'] == 'instagram':
                    # print ('Event received')
                    for output in entry:
                        output_message = output['messaging'][0]
                        sender_id = output_message['sender']['id']
                        recipient_id = output_message['recipient']['id']
                        message = output_message['message']
                        message_text = output_message['message']['text']
                        
                        #check for quick reply in message
                        if "quick_reply" in message:
                            response = quick_reply(message)
                            
                            # save in conversation summary 
                            save_to_summary(response[0], "system")                         
                            sendCustomerAMessage(app.config['PAGE_ID'],response[0],app.config['PAGE_ACCESS_TOKEN'],sender_id,response[1])
                            return make_response('EVENT_RECEIVED', 200)                     
                        else:
                            # print ('no quick reply')                            
                            conversation_id = findConversationWithASpecificUser(app.config['PAGE_ID'],sender_id,app.config['PAGE_ACCESS_TOKEN'])
                            chatHistory = getListOfAllMessageTextInConversation(conversation_id,app.config['PAGE_ACCESS_TOKEN'])
                            # chatHistory = getListOfAllMessagesInConversation(conversation_id,app.config['PAGE_ACCESS_TOKEN'])
                            output = queryIndexWithChromaFromPersistent(app.config['HARDCODED_INDEX_KEY'],message_text,chatHistory)
                            print ('this is the AI response', output)
                            response = process_response(output)
                            sendCustomerAMessage(app.config['PAGE_ID'],response[0],app.config['PAGE_ACCESS_TOKEN'],sender_id, response[1])
                            return make_response('EVENT_RECEIVED', 200)
                else:
                    return make_response('',404)
            except Exception as e:
                print ('caught exception', e)
                return make_response('',500)
            
                       
    return app
