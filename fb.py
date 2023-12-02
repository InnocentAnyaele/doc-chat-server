import requests
from config import Config
# import urllib.parse

graph_url = 'https://graph.facebook.com/v16.0'
config = Config()


def getPageIDAndPageAccessToken(user_id, user_token):
    url = f'{graph_url}/{user_id}/accounts?access_token={user_token}'
    # print (url)
    response = requests.get(url)
    # print (response.json())
    return (response.json())
    

def getPSIDAndConversationID(page_id, page_token):
    url = f'{graph_url}/{page_id}/conversations?fields=participants&access_token={page_token}'
    # print (url)
    response = requests.get(url)
    # print (response.json())
    return (response.json())

# def sendCustomerAMessage(page_id,response,page_token,psid, quick_replies = None):
#     try:
#         # print('sending customer a message')
#         message = response.replace("'",r"\'")
#         # message = response
#         # print ('this is the new response', message)
#         """
#         url = f"https://graph.facebook.com/v14.0/{page_id}/messages\
#     ?recipient={{id:{psid}}}\
#     &message={{text:'{message}'}}\
#     &messaging_type=RESPONSE\
#     &access_token={page_token}"
#         """
#         url = f"{graph_url}/{page_id}/messages?recipient={{'id':'{psid}'}}&messaging_type=RESPONSE&message={{'text':'{message}'}}&access_token={page_token}"
#         # print (url)
#         response = requests.post(url)
#         print ('send customer a responses', response.json())
#         return (response.json())
#     except Exception as e:
#         print('sendCustomerAMessage exception', e)
#         raise
    
def sendCustomerAMessage(page_id,response,page_token,psid, quick_replies = None):
    try:        
        url = f"{graph_url}/{page_id}/messages"
        # print ('this is the passed quick reply', quick_replies)
        # quick_replies =  [
        #             {
        #                 "content_type": "text",
        #                 "title": "Place an order",
        #                 "payload": {
        #                     'name': 'Innocent',
        #                     'age': 23
        #                 }
        #             }
        #         ]
        # print (url)
        
        if (quick_replies):    
            data = {
                "recipient": {
                    "id": psid
                },
                "messaging_type": "RESPONSE",
                "message": {
                    "text": response,
                    "quick_replies": quick_replies
                }
            }
        else:
            data = {
                "recipient": {
                    "id": psid
                },
                "messaging_type": "RESPONSE",
                "message": {
                    "text": response,
                }
            }
            

        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "access_token": page_token
        }

        response = requests.post(url, json=data, headers=headers, params=params)
        # print(response.json())
    except Exception as e:
        raise 'Send Customer A Message Error'

def findConversationWithASpecificUser(page_id,sender_id,page_token):
    try:
        # print('reached this function')
        url = f'{graph_url}/{page_id}/conversations?platform=instagram&user_id={sender_id}&access_token={page_token}'
        # print (url)
        response = requests.get(url)
        # print ('response', response)
        responseJSON = response.json()
        # print ('responseJSON', responseJSON)
        responseID = responseJSON['data'][0]['id'] 
        # print ('this is the responseID', responseID)
        # print (responseID)
        return (responseID)
    except Exception as e:
        # print ('findConversationWithASpecificUser exception', e)
        raise 
    

def getInformationAboutAMessage(message_id, page_token):
    # curl -i -X GET "https://graph.facebook.com/LATEST-API-VERSION/MESSAGE-ID
    # ?fields=id,created_time,from,to,message
    # &access_token=PAGE-ACCESS-TOKEN"
    try:
        url = f'{graph_url}/{message_id}?fields=id,from,to,message,created_time&access_token={page_token}'
        response = requests.get(url)
        responseJSON = response.json()
        # print ('message information', responseJSON)
        message = responseJSON['message']
        created_time = responseJSON['created_time']
        fromId = responseJSON['from']['id']
        toId = responseJSON['to']['data'][0]['id']
        # print ('check id type from', fromId)
        # print ('check id type to', toId)
        if fromId == config.INSTAGRAM_ID:
            # print('equal ids', fromId, config.INSTAGRAM_ID)
            sender = 'system'
        else:
            # print('not equal ids', fromId, config.INSTAGRAM_ID)
            sender = 'human'
        return {'sender': sender, 'message': message, 'created': created_time}
    except Exception as e:
        raise
    
def getListOfAllMessagesInConversation(conversation_id, page_token):
    try:
        url = f'{graph_url}/{conversation_id}/?fields=messages{{message,from,to,created_time}}&access_token={page_token}'
        # print (url)
        response = requests.get(url)
        # print (response.json())
        responseJSON = response.json()
        # print('all conversation message response', responseJSON)
        chatHistory = []
        messagesData = responseJSON['messages']['data']
        limit = 20
        if len(messagesData) > limit:
            messagesData = messagesData[:limit]
        for message in messagesData:
            fromId = message['from']['id']
            created_time = message['created_time']
            if fromId == config.INSTAGRAM_ID:
                chatHistory.append({'sender': 'system', 'message': message['message'], 'created_time': created_time })
            else:
                chatHistory.append({'sender': 'human', 'message': message['message'], 'created_time': created_time })
            # data = getInformationAboutAMessage(messageID, page_token)            
        # print('new chat history', chatHistory[::-1])
        return chatHistory[::-1]
    except Exception as e:
        # print ('getListOfAllMessagesWithASpecificUser exception', e)
        raise

def getListOfAllMessageTextInConversation(conversation_id,page_token):
    try:
        # url  = f'{graph_url}/{conversation_id}?fields=messages' +'{message}' +  f'&access_token={page_token}'
        url  = f'{graph_url}/{conversation_id}?fields=messages' +'{message,from,to,created_time}' +  f'&access_token={page_token}'
        # url  = f'{graph_url}/{conversation_id}?fields=from,to,messages&access_token={page_token}'
        """
            url = f"{graph_url}/{conversation_id}\
            ?fields=messages{{message}}\
            &access_token={page_token}"
        """
        # url = f"{graph_url}/{conversation_id}?fields=messages&access_token={page_token}"
        # print (url)
        response = requests.get(url)
        responseJSON = response.json()
        # print ('chat response json', responseJSON)
        messages = responseJSON['messages']['data']
        # print ('messages', messages)
        chatHistory = []
        limit = 20
        if len(messages) > limit:
            messages = messages[:limit]
        for message in messages:
            fromId = message['from']['id']
            created_time = message['created_time']
            # toId = message['to']['data'][0]['id']
            if fromId == config.INSTAGRAM_ID:
                chatHistory.append({'sender': 'system', 'message': message['message'], 'created_time': created_time })
            else:
                chatHistory.append({'sender': 'human', 'message': message['message'], 'created_time': created_time })
        # print ('chat history', chatHistory[::-1])
        return chatHistory[::-1]
    except Exception as e:
        print ('getListOfAllMessageTextInConversation exception', e)
        raise

def getLongLivedUserAccessToken(app_id,app_secret,short_lived_user_access_token):
    url = f'{graph_url}/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={short_lived_user_access_token}'
    response = requests.get(url)
    # print(response.json())
    return response.json()

def getPageAccessToken(page_id,user_access_token):
    url = f'{graph_url}/{page_id}?fields=access_token&access_token={user_access_token}'
    response = requests.get(url)
    # print(response.json())
    return response.json()

def getLongLivedPageAccessToken(user_id,long_lived_user_access_token):
    url = f'{graph_url}/{user_id}/accounts?access_token={long_lived_user_access_token}'
    response = requests.get(url)
    # print (response.json())
    return response.json()

# sampleChatHistory =  [{'sender': 'user', 'message': 'What is my name'}, {'sender': 'AI', 'message': 'Your name is Innocent.'}]

if __name__ == '__main__':
    # findConversationWithASpecificUser(config.PAGE_ID,config.SENDER_ID,config.PAGE_ACCESS_TOKEN)
    # sendCustomerAMessage(config.PAGE_ID,"test response",config.PAGE_ACCESS_TOKEN,config.SENDER_ID)
    pass
    # getPageIDAndPageAccessToken(config.USER_ID,config.USER_ACCESS_TOKEN)