import json
import re
import discord
from nltk.stem import WordNetLemmatizer as wnl 
from nltk import word_tokenize
from nltk.tokenize.treebank import TreebankWordDetokenizer
from anytree import Node, search

with open("wordbook.json", "rb") as f:
    WORDBOOK = json.load(f)

ROOT = Node("", parent=None)
for key in WORDBOOK.keys():
    words = key.split()
    parent = ROOT
    phrase = ""
    for word in words:
        phrase += f" {word}"
        word = word.lower()
        child = search.find(parent, lambda node: node.name == word, maxlevel=2)
        if child is None:
            child = Node(word, parent=parent)
        parent = child

ROOT_CHILDREN = {}
for child in ROOT.children:
    ROOT_CHILDREN[child.name] = child

Lemmatizer = wnl()
Detokenizer = TreebankWordDetokenizer()

def check_for_phrase(tokens, index):
    phrase = tokens[index].lower()
    parent = ROOT_CHILDREN[phrase]
    substitute = None
    if phrase in WORDBOOK:
        substitute = WORDBOOK[phrase]
    sub_index = index
    index += 1
    while index < len(tokens):
        child_name = tokens[index].lower()
        child = search.find(parent, lambda node: node.name == child_name, maxlevel=2)
        parent = child
        if child is None:
            break
        phrase += f" {child.name}"
        if phrase in WORDBOOK:
            substitute = WORDBOOK[phrase]
            sub_index = index
        index += 1

    return substitute, sub_index

def correct_message(s: str) -> list:
    result = []
    tokens = word_tokenize(s)
    wrong_found = False
    index = 0
    while index < len(tokens):
        token = tokens[index]
        sub = None
        if token.lower() in ROOT_CHILDREN:
            sub, sub_ind = check_for_phrase(tokens, index)
            if sub is not None:
                wrong_found = True
                sub_tokens = word_tokenize(sub)
                for sub_token in sub_tokens:
                    result.append(sub_token)
                index = sub_ind
        if sub is None:
            lemma = Lemmatizer.lemmatize(token)
            if lemma in WORDBOOK:
                wrong_found = True
                result.append(WORDBOOK[lemma])
            else:
                result.append(token)

        index += 1
    return result, wrong_found
    for token in tokens:
        lemma = Lemmatizer.lemmatize(token)
        if token in WORDBOOK:
            wrong_found = True
            result.append(WORDBOOK[token])
        elif lemma in WORDBOOK:
            wrong_found = True
            result.append(WORDBOOK[lemma])
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

    detokenized_rights = Detokenizer.detokenize(rights)
    await message.channel.send(detokenized_rights)



if __name__ == "__main__":
    with open("token.txt", 'r') as f:
        token = f.read().strip()
    client.run(token)

    # while True:
    #     s = input("Please enter a sentence: ")
    #     rights, wrong_found = correct_message(s)
    #     if not wrong_found:
    #         continue
        
    #     detoknized_rights = Detokenizer.detokenize(rights)
    #     print(detoknized_rights)
