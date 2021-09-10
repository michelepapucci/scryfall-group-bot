import logging
import re
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, MessageFilter, Filters, InlineQueryHandler
from telegram import InlineQueryResultPhoto
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class FilterQuery(MessageFilter):
    def filter(self, message):
        return re.search(".*\[\[.*\]\].*", message.text)


def howto(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="You can chat with me here or you can add me to "
                                                                    "your groupchat.\n\nWhen you send a message "
                                                                    "containing [[name of a MTG card]] I will search "
                                                                    "that card on the Scryfall MTG database and send "
                                                                    "a photo of the card.\n\nFor example, "
                                                                    "try sending me: [[counterspell]]\n\n"
                                                                    "If you want to see a "
                                                                    "preview of the sarch you can write in chat "
                                                                    "@scryfallgroupbot name of the card, you will see "
                                                                    "a collection of images corresponding to your "
                                                                    "search query.\n\nFor example, "
                                                                    "try writing: @scryfallgroupbot counter\n\n"
                                                                    "Hope I'll be useful!")


def message_query(update, context):
    try:
        found = re.search(".*\[\[(.+?)\]\].*", update.message.text)
        ploads = {'q': found.group(1)}
        r = requests.get("https://api.scryfall.com/cards/search", params=ploads)
        response = r.json()

        if int(r.status_code / 100) == 4:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Your query returned 0 result, check your "
                                                                            "spelling!")

        elif r.status_code == 200:
            if response["total_cards"] > 1:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Your query returned more than one "
                                                                                "card.This is the first result, if it "
                                                                                "isn't correct try a more specific "
                                                                                "query!")
            if "card_faces" in response["data"][0]:
                image = response["data"][0]["card_faces"][0]["image_uris"]
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=image["normal"])
                image = response["data"][0]["card_faces"][1]["image_uris"]
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=image["normal"])
            else:
                image = response["data"][0]["image_uris"]
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=image["normal"])
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="We have some internal issues, we will "
                                                                            "come back ASAP")
    except:
        context.bot.send_message(chat_id=update.effective_chat.id, text="An unexpected error has occurred! Please "
                                                                        "report this to: "
                                                                        "https://github.com/michelepapucci/scryfall"
                                                                        "-group-bot/issues")


def inline_search(update, context):
    query = update.inline_query.query
    if not query:
        return
    try:
        ploads = {'q': query}
        r = requests.get("https://api.scryfall.com/cards/search", params=ploads)
        response = r.json()
    except:
        response = False
        r = {'status_code': 500}
    results = list()
    counter = 0
    if r.status_code == 200 and response:
        if response["total_cards"] > 0:
            for card in response["data"]:
                if counter > 49:
                    break
                try:
                    results.append(
                        InlineQueryResultPhoto(
                            id=card["oracle_id"],
                            title=card["name"],
                            photo_url=card["image_uris"]["normal"],
                            thumb_url=card["image_uris"]["normal"]
                        )
                    )
                except KeyError:
                    if "card_faces" in response["data"][0]:
                        results.append(
                            InlineQueryResultPhoto(
                                id=card["oracle_id"],
                                title=card["name"],
                                photo_url=card["card_faces"][0]["image_uris"]["normal"],
                                thumb_url=card["card_faces"][0]["image_uris"]["normal"]
                            )
                        )
                    else:
                        counter = counter - 1
                counter = counter + 1
            update.inline_query.answer(results)


key = os.environ['TELEGRAM_APY_KEY']

updater = Updater(token=key, use_context=True)
dispatcher = updater.dispatcher

howto_handler = CommandHandler('howto', howto)
dispatcher.add_handler(howto_handler)

query_syntax_filter = FilterQuery()
message_handler = MessageHandler(Filters.text & query_syntax_filter, message_query)
dispatcher.add_handler(message_handler)

inline_search_handler = InlineQueryHandler(inline_search)
dispatcher.add_handler(inline_search_handler)

try:
    if __name__ == "__main__":
        updater.start_polling()
        updater.idle()
except KeyboardInterrupt:
    print("closing")
