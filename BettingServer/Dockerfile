FROM python:3.13-slim
WORKDIR /BettingApp/
COPY ./requirements.txt ./socket_test.py ./launch.sh /BettingApp/
RUN ["python", "-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt"]
RUN ["python", "-m", "pip", "install", "--no-cache-dir", "gunicorn", "gevent", "requests_unixsocket"]
COPY ./app /BettingApp/app/
RUN ["pybabel", "compile", "-d", "./app/assets/translations"]
RUN ["chmod", "+x", "./launch.sh"]
ENTRYPOINT ["./launch.sh"]
HEALTHCHECK --interval=5s --timeout=30s --start-period=5s --retries=2 CMD [ "python", "./socket_test.py" ]
