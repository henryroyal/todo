FROM python

RUN pip install uwsgi
ADD . /app
WORKDIR /app
RUN pip install -r requirements.txt &&  \
    pip install -r requirements-dev.txt && \
    chown -R daemon:daemon /app
EXPOSE 8000
CMD ["uwsgi", "--uid=1", "--gid=1", "--http", "0.0.0.0:8000", "--master", "-p", "4", "-w", "src.wsgi:app"]
