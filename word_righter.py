import json
import re
import discord
from nltk.stem.snowball import SnowballStemmer 
from nltk import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer

with open("wordbook.json", "rb") as f:
    WORDBOOK = json.load(f)

Stemmer = SnowballStemmer("english")

def correct_message(s: str) -> list:
    result = []
    tokens = word_tokenize(s)
    wrong_found = False
    for token in tokens:
        stem = Stemmer.stem(token)
        if stem in WORDBOOK:
            wrong_found = True
            result.append(WORDBOOK[stem])
        elif token in WORDBOOK:
            wrong_found = True
            result.append(WORDBOOK[token])
        else:
            result.append(token)

    return result, wrong_found


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged on as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    rights, wrong_found = correct_message(message.content)
    if not wrong_found:
        return

    detokenizer = TreebankWordDetokenizer()
    detokenized_rights = detokenizer.detokenize(rights)
    await message.channel.send(detokenized_rights)


with open("token.txt", 'r') as f:
    token = f.read().strip()
client.run(token)
