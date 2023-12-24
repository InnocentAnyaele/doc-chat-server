import json
import re
import random
from utils import save_to_summary

def quick_reply(message):
    try:
        quick_reply_payload = message['quick_reply']['payload']
        quick_reply_text = message['text']
        # print ('quick reply payload', message)
        print ('This is the quick reply text', quick_reply_text)
        quick_reply_payload = quick_reply_payload.replace("'",'"')
        quick_reply_payload = json.loads(quick_reply_payload)
        # print ('checking json', quick_reply_payload)
        # print ('checking json', quick_reply_payload["type"])
        
        save_to_summary(quick_reply_text, "human")
        
        if quick_reply_payload["type"] == 'about_business':
            return ["This business specializes in coffee paste, providing a convenient way for consumers to enjoy a café-style coffee experience at home. The coffee paste is shipped in a cool box to ensure freshness.", None]
        if quick_reply_payload["type"] == 'speak_agent':
            return ["An agent will be in touch with you shortly", None]
        if quick_reply_payload["type"] == 'about_product':
            return ["We have 5 flavors of coffee paste available: Original (unflavored), Hazelnut, Vanilla, Chocolate, and Caramel.", None]
        if quick_reply_payload["type"] == 'place_order':
            return ["Sure! I can assist you with that. Please provide the following details for your order: Name, Flavour, Quantity, Primary Contact, Secondary Contact, and Delivery Address", None]
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
                return [orderConfirmedResponse, quick_reply]
                # sendCustomerAMessage(app.config['PAGE_ID'],orderConfirmedResponse,app.config['PAGE_ACCESS_TOKEN'],sender_id,quick_reply)
        if quick_reply_payload['type'] == 'pay_with_ai':
            orderID = quick_reply_payload['order']['orderID']
            pay_with_ai_response = f"Pay through our bank with the reference {orderID} and send a screenshot of your payment. Bank details are NAME - Montado (pvt) ltd, ACCOUNT - 047010020567, BANK - HNB Biyagama."
            return [pay_with_ai_response, None]
            # sendCustomerAMessage(app.config['PAGE_ID'],pay_with_ai_response,app.config['PAGE_ACCESS_TOKEN'],sender_id)
        if quick_reply_payload['type'] == 'pay_with_web':
            pay_with_web_response = "Pay through our website example.com"
            return [pay_with_web_response, None]
            # sendCustomerAMessage(app.config['PAGE_ID'],pay_with_web_response,app.config['PAGE_ACCESS_TOKEN'],sender_id)          
    except Exception as e:
        print(e)
        raise Exception(e)
        
        
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
                if key not in json_order or not json_order[key]:
                    missing_details.append(full_order_name[key])
                # if key not in json_order:
                #     return False
                # else:
                #     # do extra validations here
                #     if not json_order[key]:
                #         missing_details.append(full_order_name[key])
            
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
    

def process_response(output):
    try:
        validate_output = validate_order(output)
        if not validate_output:
            return [output, None]
            # sendCustomerAMessage(app.config['PAGE_ID'],output,app.config['PAGE_ACCESS_TOKEN'],sender_id)
        elif validate_output['status'] == 'complete':
            # if output[0] == '{':
            json_order = validate_output['msg']
            orderID = random.randint(100000, 999999)
            json_order["orderID"] = orderID
            # print ('JSON Order', json_order)
            order_response = f"Select button to confirm your order. Order details are {json_order['name']}, {json_order['flavour']}, {json_order['quantity']}, {json_order['contact1']}, {json_order['contact2']}, {json_order['address']}"
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
            save_to_summary(order_response, "system")
            return [order_response, quick_reply]
            # sendCustomerAMessage(app.config['PAGE_ID'],order_response,app.config['PAGE_ACCESS_TOKEN'],sender_id,quick_reply)
        elif validate_output['status'] == 'incomplete':
            msg = validate_output['msg']
            save_to_summary(msg, "system")
            return [msg, None]
            # sendCustomerAMessage(app.config['PAGE_ID'],msg,app.config['PAGE_ACCESS_TOKEN'],sender_id)
    except Exception as e:
        raise Exception(e)
    # return