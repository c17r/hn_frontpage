FROM c17r/py3-app AS base

ADD . /code/
WORKDIR /code/

RUN /venv/bin/pip install --quiet --no-cache-dir -r _requirements/default.txt

CMD ["/venv/bin/python", "main.py"]
