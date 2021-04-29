FROM python:3.8-alpine

WORKDIR /app

COPY setup.py /app
COPY sailor_hat/ /app/sailor_hat/

RUN python3 setup.py install

ENTRYPOINT [ "/usr/local/bin/sailor-hat-daemon" ]
