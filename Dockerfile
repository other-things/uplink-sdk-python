FROM python:2-slim
RUN apt-get update && apt-get install -y gcc python-dev
WORKDIR /usr/src/app

COPY requirements.txt ./
COPY dev-requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt

COPY . .

ENTRYPOINT [ "pytest", "-vv", "-s", "integration_tests" ]
