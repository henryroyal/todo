FROM python

RUN pip install uwsgi
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt &&  \
    pip install -r requirements-dev.txt && \
    chown daemon:daemon /app
EXPOSE 8000
USER daemon
CMD ["uwsgi", "--http", "0.0.0.0:8000", "--master", "-p", "4", "-w", "src.wsgi:app"]
