
FROM python
# Adjust Time Zone
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN addgroup --system app && adduser --system --group app
USER app
ENV PATH="$PATH:/home/app/.local/bin"

# Add files
COPY . /app


# Go to working directory
WORKDIR /app

# Install requirements
# RUN apk add --update py-pip

RUN pip install --upgrade pip
# test, lint and coverage packages
RUN pip install pytest pytest-cov coverage pylint
# app dependencies
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD [ "gunicorn", "--bind" , "0.0.0.0:5000", "routing:app" ]

