FROM c17r/py3-app AS base

ADD . /code/
WORKDIR /code/

RUN /venv/bin/pip install --quiet --no-cache-dir -r _requirements/prod.txt

CMD ["/venv/bin/python", "main.py"]
