FROM python:3.10-slim-buster
COPY . ./kinguin_bot
WORKDIR /kinguin_bot
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --user -r requirements.txt

CMD [ "python", "aiogram_bot.py" ]