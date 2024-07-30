FROM python:3.11.9-alpine
COPY . ./kinguin_bot
WORKDIR /kinguin_bot

RUN pip install --upgrade pip && pip install --user --no-warn-script-location --no-cache-dir -r requirements.txt

CMD [ "python", "aiogram_bot.py" ]