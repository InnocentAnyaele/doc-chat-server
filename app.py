from flask import Flask, request, make_response
from config import TestConfig
from functools import wraps
import os
import uuid
from werkzeug.utils import secure_filename
from utils import delete_context, createIndex, checkExtension
import threading

def create_app(config = TestConfig):
    app = Flask(__name__)
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
        return "Hello, World"

    
    @app.route('/api/addData')
    @token_required
    def add_data():
        if request.method == 'POST':
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
                    
                t = threading.Thread(target=delete_context, args=(uniqueDirName))
                t.start()
                
                extension = checkExtension(fileNamesArray[-1]) 
                
                if extension == 'pdf':
                    path_to_pdf = os.path.join(uniqueDirName,fileNamesArray[-1])
                    indexKey = createIndex(path_to_pdf)
                    response = make_response(indexKey)
                    response.status_code = 200
                    return response
                else:
                    response = make_response(extension , 'is not accepted')
                    response.status_code = 400
                    return (response)
            except Exception as e:
                print (e)
                response = make_response('Something went wrong')
                response.status_code = 500
                return response
                
    
    return app