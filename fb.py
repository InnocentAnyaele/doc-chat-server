import requests
from config import Config
# import urllib.parse

graph_url = 'https://graph.facebook.com/v16.0'
config = Config()


def getPageIDAndPageAccessToken(user_id, user_token):
    url = f'{graph_url}/{user_id}/accounts?access_token={user_token}'
    print (url)
    response = requests.get(url)
    print (response.json())
    return (response.json())
    

def getPSIDAndConversationID(page_id, page_token):
    url = f'{graph_url}/{page_id}/conversations?fields=participants&access_token={page_token}'
    print (url)
    response = requests.get(url)
    print (response.json())
    return (response.json())

def sendCustomerAMessage(page_id,response,page_token,psid):
    new_response = response.replace("'",r"\'")
    print ('this is the new response', new_response)
    url = f"https://graph.facebook.com/v14.0/{page_id}/messages\
?recipient={{id:{psid}}}\
&message={{text:'{new_response}'}}\
&messaging_type=RESPONSE\
&access_token={page_token}"
    print (url)
    response = requests.post(url)
    print (response.json())
    return (response.json())

def findConversationWithASpecificUser(page_id,sender_id,page_token):
    url = f'{graph_url}/{page_id}/conversations?platform=instagram&user_id={sender_id}&access_token={page_token}'
    print (url)
    response = requests.get(url)
    responseJSON = response.json()
    responseID = responseJSON['data'][0]['id'] 
    print (responseID)
    return (responseID)

def getListOfAllMessagesInConversation(conversation_id,page_token):
    url = f'{graph_url}/{conversation_id}/?fields=messages&access_token={page_token}'
    print (url)
    response = requests.get(url)
    print (response.json())
    return (response.json())

def getListOfAllMessageTextInConversation(conversation_id,page_token):
    # url  = f'{graph_url}/{conversation_id}?fields=messages' +'{message}' +  f'&access_token={page_token}'
    url = f"{graph_url}/{conversation_id}\
?fields=messages{{message}}\
&access_token={page_token}"
    print (url)
    response = requests.get(url)
    responseJSON = response.json()
    print (responseJSON)
    messages = responseJSON['messages']['data']
    chatHistory = []
    chatHistoryWithoutIndication = []
    for message in messages:
        chatHistory.append({'sender': 'human', 'message' : message['message']})
        chatHistoryWithoutIndication.append(message['message'])
    print (responseJSON)
    print (chatHistory)
    return (chatHistory)

# sampleChatHistory =  [{'sender': 'user', 'message': 'What is my name'}, {'sender': 'AI', 'message': 'Your name is Innocent.'}]

if __name__ == '__main__':
    # findConversationWithASpecificUser(config.PAGE_ID,config.SENDER_ID,config.PAGE_ACCESS_TOKEN)
    sendCustomerAMessage(config.PAGE_ID,"test response",config.PAGE_ACCESS_TOKEN,config.SENDER_ID)
    # pass