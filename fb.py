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
    
def sendCustomerAMessage(page_id,response,page_token,psid, quick_replies = []):
    try:        
        url = f"{graph_url}/{page_id}/messages"
        quick_replies =  [
                    {
                        "content_type": "text",
                        "title": "Place an order",
                        "payload": "#Order"
                    }
                ]
        print (url)
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

        headers = {
            "Content-Type": "application/json"
        }
        params = {
            "access_token": page_token
        }

        response = requests.post(url, json=data, headers=headers, params=params)
        print(response.json())
    except Exception as e:
        raise 'Send Customer A Message Error'

def findConversationWithASpecificUser(page_id,sender_id,page_token):
    try:
        print('reached this function')
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
        print ('findConversationWithASpecificUser exception', e)
        raise 

def getListOfAllMessagesInConversation(conversation_id, page_token):
    try:
        url = f'{graph_url}/{conversation_id}/?fields=messages&access_token={page_token}'
        print (url)
        response = requests.get(url)
        # print (response.json())
        responseJSON = response.json()
        print('responseJSON', responseJSON)
        return responseJSON
    except Exception as e:
        print ('getListOfAllMessagesWithASpecificUser exception', e)
        raise

def getListOfAllMessageTextInConversation(conversation_id,page_token):
    try:
        url  = f'{graph_url}/{conversation_id}?fields=messages' +'{message}' +  f'&access_token={page_token}'
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
        chatHistoryWithoutIndication = []
        if len(messages) > 10:
            messages = messages[-10:len(messages)]
        for message in messages:
            chatHistory.append({'sender': 'human', 'message': message['message']})
            chatHistoryWithoutIndication.append(message['message'])
        # print ('chat history', chatHistory)
        return chatHistory
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