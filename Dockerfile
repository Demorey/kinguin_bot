FROM python:3.11.8-slim-bullseye
COPY . ./kinguin_bot
WORKDIR /kinguin_bot

RUN pip install --upgrade pip
RUN pip install --user --no-warn-script-location -r requirements.txt

CMD [ "python", "aiogram_bot.py" ]