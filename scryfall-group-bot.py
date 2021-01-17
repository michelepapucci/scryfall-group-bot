import logging
import re
import requests
import json
from telegram.ext import Updater, CommandHandler, MessageHandler, MessageFilter, Filters
from pathlib import Path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class FilterQuery(MessageFilter):
    def filter(self, message):
        return re.search(".*\[\[.*\]\].*", message.text)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Write [[Name of a MTG card]] to receive an image"
                                                                    " of the card available on Skryfall")


def message_query(update, context):
    found = re.search(".*\[\[(.+?)\]\].*", update.message.text)
    ploads = {'q': found.group(1)}
    r = requests.get("https://api.scryfall.com/cards/search", params=ploads)
    response = r.json()

    if r.status_code == 404:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your query returned 0 result, check your "
                                                                        "spelling!")

    elif r.status_code == 200:
        if response["total_cards"] > 1:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Your query returned more than one card. "
                                                                            "This is the first result, if it isn't "
                                                                            "correct try a more specific query!")
        card = response["data"][0]["image_uris"]
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=card["normal"])

    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="An error has occurred!")


token_file = open(Path('conf/token.json'))
token_json = json.load(token_file)
token_file.close()
updater = Updater(token=token_json["token"], use_context=True)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

query_syntax_filter = FilterQuery()
message_handler = MessageHandler(Filters.text & query_syntax_filter, message_query)
dispatcher.add_handler(message_handler)

if __name__ == "__main__":
    updater.start_polling()
