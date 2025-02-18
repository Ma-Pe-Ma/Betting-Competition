FROM python:3.13-slim
RUN apt-get update && apt-get install -y nginx && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /BettingApp/
COPY ./app /BettingApp/app/
COPY ./requirements.txt /BettingApp/
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN python -m pip install --no-cache-dir gunicorn gevent
RUN pybabel compile -d ./app/assets/translations
RUN mkdir -p /BettingInstance/
COPY ./deployment/configuration.json /BettingInstance/
RUN python -m flask --app 'app:create_app(instance_path="/BettingInstance/")' init-db
COPY ./deployment/nginx.conf ./deployment/launch.sh /BettingApp/
RUN ["chmod", "+x", "./launch.sh"]
ENTRYPOINT ["./launch.sh"]
EXPOSE 80
EXPOSE 443
