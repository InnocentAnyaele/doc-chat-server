from flask import Flask, request, make_response
from config import DevelopmentConfig
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
from utils import createIndex, checkExtension, startDeleteThread, queryPineconeIndex, queryIndexWithChromaFromPersistent
from fb import findConversationWithASpecificUser, getListOfAllMessageTextInConversation, sendCustomerAMessage, getListOfAllMessagesInConversation
from flask_cors import CORS
import json
import random
import re


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
                
                
    # @app.route('/webhook/webhook', methods = ['POST'])
    # def messagingWebhook():
    #     print ('reached the webhook')
    #     body = request.get_json()
    #     print (body)
    #     print(body)
    #     if body['object'] == 'page':
    #         return make_response('EVENT_RECEIVED', 200)
    #     else:
    #         return make_response('',404)
        
    @app.route('/webhook/messaging-webhook', methods=['GET','POST'])
    def messagingWebhook():
        if request.method == 'GET':
            # print ('reached the messaging webhook')
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
            # print ('reached the webhook')
            body = request.get_json()
            # print ('this is the body',body)
            entry = body['entry']
            # print ('webhook entry', entry)
            # print (entry[0])
            
            try:
                if body['object'] == 'instagram':
                    # print ('Event received')
                    for output in entry:
                        output_message = output['messaging'][0]
                        sender_id = output_message['sender']['id']
                        recipient_id = output_message['recipient']['id']
                        message = output_message['message']
                        message_text = output_message['message']['text']
                        # print ('reached parsing the entry')
                        # print ('sender ID', sender_id)
                        # print ('recipient ID', recipient_id)
                        # print ('messsage_text', message_text)
                        
                        #check for quick reply in message
                        if "quick_reply" in message:
                            quick_reply_payload = message['quick_reply']['payload']
                            # print ('quick reply payload', quick_reply_payload)
                            quick_reply_payload = quick_reply_payload.replace("'",'"')
                            quick_reply_payload = json.loads(quick_reply_payload)
                            # print ('checking json', quick_reply_payload)
                            # print ('checking json', quick_reply_payload["type"])
                            if quick_reply_payload["type"] == 'confirm_order':
                                    orderID = quick_reply_payload['order']['orderID']
                                    orderConfirmedResponse = f"Your order has been placed with the id of {orderID}. Select your payment method"
                                    ai_payload = {
                                        "type": 'pay_with_ai',
                                        "order": quick_reply_payload['order'], 
                                    }
                                    website_payload = {
                                        "type": 'pay_with_web',
                                        "order": quick_reply_payload['order'], 
                                    }
                                    quick_reply = [{
                                        "content_type": "text",
                                        "title": f"Pay with AI",
                                        "payload": f"{ai_payload}"
                                    },     {
                                        "content_type": "text",
                                        "title": f"Pay through website",
                                        "payload": f"{website_payload}"
                                    }]
                                    sendCustomerAMessage(app.config['PAGE_ID'],orderConfirmedResponse,app.config['PAGE_ACCESS_TOKEN'],sender_id,quick_reply)
                            if quick_reply_payload['type'] == 'pay_with_ai':
                                orderID = quick_reply_payload['order']['orderID']
                                pay_with_ai_response = f"Pay through our bank with the reference {orderID} and send a screenshot of your payment. Bank details are NAME - Montado (pvt) ltd, ACCOUNT - 047010020567, BANK - HNB Biyagama."
                                sendCustomerAMessage(app.config['PAGE_ID'],pay_with_ai_response,app.config['PAGE_ACCESS_TOKEN'],sender_id)
                            if quick_reply_payload['type'] == 'pay_with_web':
                                pay_with_web_response = "Pay through our website example.com"
                                sendCustomerAMessage(app.config['PAGE_ID'],pay_with_web_response,app.config['PAGE_ACCESS_TOKEN'],sender_id)                                
                        else:
                            # print ('no quick reply')                            
                            conversation_id = findConversationWithASpecificUser(app.config['PAGE_ID'],sender_id,app.config['PAGE_ACCESS_TOKEN'])
                            chatHistory = getListOfAllMessageTextInConversation(conversation_id,app.config['PAGE_ACCESS_TOKEN'])
                            # chatHistory = getListOfAllMessagesInConversation(conversation_id,app.config['PAGE_ACCESS_TOKEN'])
                            output = queryIndexWithChromaFromPersistent(app.config['HARDCODED_INDEX_KEY'],message_text,chatHistory)
                            print ('this is the AI response', output)
                            
                            # def get_order_details(output):
                            #     try:
                            #         print ('processing output', output)
                            #         if len(output) > 15 and output[:15] == 'ORDERPLACED4564':
                            #             print ('json order part', output[16:])
                            #             json_order = json.loads(output[16:])
                            #             print ('json order part after processing', json_order)
                            #             print ('name', json_order['name'])
                            #             return (True, json_order)
                            #     except Exception as e:
                            #         return (False, {})
                                
                                 
                            def validate_order(output):
                                try:
                                    print ('reached get order_details', output)
                                    if output.startswith('0RD3R9LAC3D'):
                                        full_order_name = {
                                            "name": "Name",
                                            "flavour": "Flavour",
                                            "quantity": "Quantity",
                                            "contact1": "Primary Contact",
                                            "contact2": "Secondary Contact",
                                            "address" : "Address" 
                                        }
                                        pattern = re.compile(r'{.*}', re.DOTALL)
                                        matches = pattern.findall(output)
                                        json_order = json.loads(matches[0])
                                        missing_details = []
                                        print ('json order from reg output', json_order)
                                        required_keys = ["name", "flavour", "quantity", "contact1", "contact2", "address"]
                                        for key in required_keys:
                                            if key not in json_order:
                                                return False
                                            else:
                                                # do extra validations here
                                                if not json_order[key]:
                                                    missing_details.append(full_order_name[key])
                                        
                                        print ('missing details', missing_details)
                                        if len(missing_details) > 0:
                                            details = ''
                                            for i in range(len(missing_details)):
                                                detail = missing_details[i]
                                                if i == len(missing_details) - 1:
                                                    details = details + f' {detail}.'
                                                else:
                                                    details = details + f' {detail},'
                                                    
                                            msg = f'Your order is missing the following details:{details}'
                                            print ('missing details message', msg)
                                            response = {
                                                'status': 'incomplete',
                                                'msg': msg
                                            }
                                            return response
                                        else:
                                            response = {
                                                'status': 'complete',
                                                'msg': json_order
                                            }
                                            return response
                                    else:
                                        return False
                                except Exception as e:
                                    print (e)
                                    return False
                                
                            #process response
                            def process_response():
                                # return
                                validate_output = validate_order(output)
                                if not validate_output:
                                    sendCustomerAMessage(app.config['PAGE_ID'],output,app.config['PAGE_ACCESS_TOKEN'],sender_id)
                                elif validate_output['status'] == 'complete':
                                    # if output[0] == '{':
                                    json_order = validate_output['msg']
                                    orderID = random.randint(100000, 999999)
                                    json_order["orderID"] = orderID
                                    # print ('JSON Order', json_order)
                                    order_response = f"Select button to confirm your order. Order details are {json_order['name']}, {json_order['flavour']}, {json_order['quantity']}, {json_order['contact1']}, {json_order['contact2']}, {json_order['address']}"
                                    #temporary save order ID and order data - with status of confirmed
                                    # payment_response = "Order sent. Your order ID is 18732. You can either pay to our bank or website (example.com). Bank details are NAME - Montado (pvt) ltd, ACCOUNT - 047010020567, BANK - HNB Biyagama. Kindly use your ID as reference."
                                    payload = {
                                        "type": "confirm_order",
                                        "order": json_order
                                    }
                                    quick_reply = [
                                                {
                                                    "content_type": "text",
                                                    "title": f"Confirm order",
                                                    "payload": f"{payload}"
                                                }
                                            ]
                                    sendCustomerAMessage(app.config['PAGE_ID'],order_response,app.config['PAGE_ACCESS_TOKEN'],sender_id,quick_reply)
                                elif validate_output['status'] == 'incomplete':
                                    msg = validate_output['msg']
                                    sendCustomerAMessage(app.config['PAGE_ID'],msg,app.config['PAGE_ACCESS_TOKEN'],sender_id)
                                # if validate_output and validate_output['status'] == 'complete':
                                # # if output[0] == '{':
                                #     json_order = validate_output['msg']
                                #     orderID = random.randint(100000, 999999)
                                #     json_order["orderID"] = orderID
                                #     # print ('JSON Order', json_order)
                                #     order_response = f"Kindly select the reply to confirm your order."
                                #     #temporary save order ID and order data - with status of confirmed
                                #     # payment_response = "Order sent. Your order ID is 18732. You can either pay to our bank or website (example.com). Bank details are NAME - Montado (pvt) ltd, ACCOUNT - 047010020567, BANK - HNB Biyagama. Kindly use your ID as reference."
                                #     payload = {
                                #         "type": "confirm_order",
                                #         "order": json_order
                                #     }
                                #     quick_reply = 
                                #                 {
                                #                     "content_type": "text",
                                #                     "title": f"Confirm order",
                                #                     "payload": f"{payload}"
                                #                 }
                                #             ]
                                #     sendCustomerAMessage(app.config['PAGE_ID'],order_response,app.config['PAGE_ACCESS_TOKEN'],sender_id,quick_reply)
                                # elif validate_output and validate_output['status'] == 'incomplete':
                                #     msg = validate_output['msg']
                                #     sendCustomerAMessage(app.config['PAGE_ID'],msg,app.config['PAGE_ACCESS_TOKEN'],sender_id)
                                # else:
                                #     sendCustomerAMessage(app.config['PAGE_ID'],output,app.config['PAGE_ACCESS_TOKEN'],sender_id)
                            process_response()
                        return make_response('EVENT_RECEIVED', 200)
                else:
                    return make_response('',404)
            except Exception as e:
                print ('caught exception', e)
                return make_response('',500)
            
                       
    return app
