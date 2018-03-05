from os import listdir
from os.path import join, isfile
from collections import defaultdict

import pickle
import re
from PorterStemmer import PorterStemmer


def extract_documents():
    file_names = sorted([f for f in listdir('./Dataset/') if isfile(join('./Dataset/', f)) and f.endswith('.sgm')])
    documents = []
    for f in file_names:
        with open('./Dataset/' + f, 'r', encoding='utf-8', errors='ignore') as pointer:
            sgm_file = pointer.read()
            # Find all documents
            all_docs = re.findall(r'<REUTERS(.*?)</REUTERS>', sgm_file, re.DOTALL)
            # Extract ids and headers
            headers = [re.search(r'<TEXT(.*?)</TEXT>', doc, re.DOTALL).groups(0)[0] for doc in all_docs]
            for header in headers:
                if 'TYPE="BRIEF"' in header:
                    document = re.search(r'<TITLE>(.*?)</TITLE>', header, re.DOTALL).groups(0)[0]
                elif 'TYPE="UNPROC"' in header:
                    document = re.search(r'&#2;(.*?)&#3;', header, re.DOTALL).groups(0)[0]
                else:
                    title_and_body = re.search(r'<TITLE>(.*?)</TITLE>.*?<BODY>(.*?)</BODY>', header, re.DOTALL).groups(
                        0)
                    document = title_and_body[0] + ' ' + title_and_body[1]
                document = document.replace('&lt;', ' ')
                document = document.replace('&gt;', ' ')
                document = document.replace('&ge;', ' ')
                document = document.replace('&le;', ' ')
                document = document.replace('&#127;', ' ')
                document = document.replace('&#3;', ' ')
                document = document.replace('&amp;', ' ')
                document = document.replace('&#;', ' ')
                document = re.sub('\W', ' ', document)
                document = re.sub(r'\d+', ' ', document)
                document = document.lower().strip()
                # No need for the id now
                documents.append(document)
    return documents


def tokenize(documents):
    stop_word_set = set(open('./stopwords.txt', 'r').read().split())
    p = PorterStemmer()
    word_to_doc = defaultdict(lambda: defaultdict(list))  # Positional inverted index
    for article_index, document in enumerate(documents, start=1):
        for word_index, word in enumerate(document.split()):
            if word not in stop_word_set:
                stemmed_word = p.stem(word, 0, len(word) - 1)
                word_to_doc[stemmed_word][article_index].append(word_index)

    return word_to_doc


def create_index_files(word_to_doc):
    word_to_index = {word: index for index, word in enumerate(list(word_to_doc.keys()))}
    postings_lists = {word_to_index[word]: word_to_doc[word] for word in word_to_doc.keys()}
    pickle.dump(word_to_index, open('word_to_index.pkl', 'wb'))
    pickle.dump(postings_lists, open('postings_lists.pkl', 'wb'))


def main():
    documents = extract_documents()
    word_to_doc = tokenize(documents)
    create_index_files(word_to_doc)


if __name__ == "__main__":
    main()
