# FROM python:3.10.11-alpine3.16
FROM python:3.10.11-alpine3.17
RUN apk update && apk add git
RUN apk add -u zlib-dev jpeg-dev
RUN apk add build-base gcc abuild binutils binutils-doc gcc-doc libffi-dev
RUN pip install --default-timeout=100 torch==2.0.0+cpu torchvision==0.15.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD [ "flask", "run", "--host=0.0.0.0", "--port=5000", "--debugger", "--reload" ]

