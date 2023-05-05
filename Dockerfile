FROM python:3.10.11
WORKDIR /GPTContextServer
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

# CMD ["python", "./utils.py"]
# CMD ["flask", "run", "--debug"]

CMD [ "flask", "run", "--host=0.0.0.0", "--port=5000", "--debugger", "--reload" ]



