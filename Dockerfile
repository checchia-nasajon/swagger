FROM python
FROM nginx:1.21-alpine
# Adjust Time Zone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apk update && apk add --no-cache "nodejs>=14.17.6-r0"
RUN addgroup --system app && adduser --system --group app
USER app
ENV PATH="$PATH:/home/app/.local/bin"
ENV API_KEY "**None**"
ENV SWAGGER_JSON "/app/swagger.json"
ENV PORT 8080
ENV BASE_URL ""
ENV SWAGGER_JSON_URL ""

# Add files
COPY . /app
COPY ./docker/nginx.conf ./docker/cors.conf /etc/nginx/
COPY ./dist/* /usr/share/nginx/html/
COPY ./docker/run.sh /usr/share/nginx/
COPY ./docker/configurator /usr/share/nginx/configurator

# Go to working directory
WORKDIR /app

# Install requirements
# RUN apk add --update py-pip

RUN pip install --upgrade pip
# test, lint and coverage packages
RUN chmod +x /usr/share/nginx/run.sh && \
    chmod -R a+rw /usr/share/nginx && \
    chmod -R a+rw /etc/nginx && \
    chmod -R a+rw /var && \
    chmod -R a+rw /var/run

RUN pip install pytest pytest-cov coverage pylint
# app dependencies
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080

CMD ["sh", "/usr/share/nginx/run.sh"]