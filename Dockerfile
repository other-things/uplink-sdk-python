FROM python:2-slim
RUN apt-get update && apt-get install -y gcc python-dev libffi6 libffi-dev
WORKDIR /usr/src/app

COPY requirements.txt ./
COPY dev-requirements.txt ./
RUN pip install pipenv
RUN pipenv install

COPY . .

ENTRYPOINT [ "pipenv", "run", "pytest", "-vv", "-s", "integration_tests" ]
