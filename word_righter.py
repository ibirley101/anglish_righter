import json
import re
import discord
from nltk.stem import WordNetLemmatizer as wnl
from nltk import word_tokenize
from nltk.tag import pos_tag
from nltk.tokenize.treebank import TreebankWordDetokenizer
from anytree import Node, search
from lemminflect import getInflection


Lemmatizer = wnl()
Detokenizer = TreebankWordDetokenizer()

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


def treebank_to_wnl(tag):
    if tag.startswith("N"):
        return 'n'
    elif tag.startswith("V"):
        return 'v'
    elif tag.startswith("J"):
        return 'a'
    elif tag.startswith("R"):
        return 'r'
    return 's'

def read_wordbook(word, tag):
    entry = WORDBOOK[word]
    if type(entry) is str:
        replacement = getInflection(entry, tag=tag)
        if not replacement:
            return entry
        return replacement[0]
    
    # type is dictionary
    if tag in entry:
        return entry[tag]

    # couldn't find a replacement
    return word


def check_for_phrase(tagged_tokens, index):
    phrase = tagged_tokens[index][0].lower()
    tag = tagged_tokens[index][1]
    parent = ROOT_CHILDREN[phrase]
    substitute = None
    if phrase in WORDBOOK:
        substitute = read_wordbook(phrase, tag)
    sub_index = index
    index += 1
    while index < len(tagged_tokens):
        child_name = tagged_tokens[index][0].lower()
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
    tagged_tokens = pos_tag(tokens)
    wrong_found = False
    index = 0
    while index < len(tokens):
        token = tagged_tokens[index][0]
        tag = tagged_tokens[index][1]
        sub = None
        if token.lower() in ROOT_CHILDREN:
            sub, sub_ind = check_for_phrase(tagged_tokens, index)
            if sub is not None:
                wrong_found = True
                sub_tokens = word_tokenize(sub)
                for sub_token in sub_tokens:
                    result.append(sub_token)
                index = sub_ind
        if sub is None:
            lemma = Lemmatizer.lemmatize(token)
            if lemma == token:
                pos = treebank_to_wnl(tag)
                lemma = Lemmatizer.lemmatize(token, pos)
            if lemma in WORDBOOK:
                wrong_found = True
                substitute = read_wordbook(lemma, tag)
                result.append(substitute)
            else:
                result.append(token)

        index += 1
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
    with open("token.txt", "r") as f:
        token = f.read().strip()
    client.run(token)

    # while True:
    #     s = input("Please enter a sentence: ")
    #     rights, wrong_found = correct_message(s)
    #     if not wrong_found:
    #         continue

    #     detoknized_rights = Detokenizer.detokenize(rights)
    #     print("\n\n")
    #     print(detoknized_rights)
