import time
import os
import shutil

def createIndex(path='./data/SamplePDF.pdf'):
    
    return 'indexKey'

def delete_context(dirName):
    time.sleep(300)
    if os.path.exists(dirName):
        shutil.rmtree(dirName)
    else:
        print('Path does not exist')
        
    return 'completed'

def checkExtension(fileName):
    fileName_split = fileName.split('.')
    fileExtension = fileName_split[-1]
    return fileExtension