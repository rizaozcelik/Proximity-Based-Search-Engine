import pickle
import re
from collections import defaultdict
from os import listdir
from os.path import join, isfile

from PorterStemmer import PorterStemmer


# This method is responsible to extract documents to index. Note that there are three types of text documents called
# as Brief, unproc and a regular one in the Reuters dataset.
def extract_documents():
    # Retrieve the .sgm files in the folder.
    file_names = sorted([f for f in listdir('./Dataset/') if isfile(join('./Dataset/', f)) and f.endswith('.sgm')])
    # This list will store all the documents that would be indexed.
    documents = []
    for f in file_names:
        with open('./Dataset/' + f, 'r', encoding='utf-8', errors='ignore') as pointer:
            # Read the the file
            sgm_file = pointer.read()
            # Find all documents enclosed between REUTERS tags.
            all_docs = re.findall(r'<REUTERS(.*?)</REUTERS>', sgm_file, re.DOTALL)
            # Extract headers of the documents by TEXT tags
            headers = [re.search(r'<TEXT(.*?)</TEXT>', doc, re.DOTALL).groups(0)[0] for doc in all_docs]
            # Extract the content from each corresponding document type.
            for header in headers:
                if 'TYPE="BRIEF"' in header:
                    document = re.search(r'<TITLE>(.*?)</TITLE>', header, re.DOTALL).groups(0)[0]
                elif 'TYPE="UNPROC"' in header:
                    document = re.search(r'&#2;(.*?)&#3;', header, re.DOTALL).groups(0)[0]
                else:
                    # Store title and body together as a single document
                    title_and_body = re.search(r'<TITLE>(.*?)</TITLE>.*?<BODY>(.*?)</BODY>', header, re.DOTALL).groups(
                        0)
                    document = title_and_body[0] + ' ' + title_and_body[1]
                # Remove some special characters in the text
                document = document.replace('&lt;', ' ')
                document = document.replace('&gt;', ' ')
                document = document.replace('&ge;', ' ')
                document = document.replace('&le;', ' ')
                document = document.replace('&#127;', ' ')
                document = document.replace('&#3;', ' ')
                document = document.replace('&amp;', ' ')
                document = document.replace('&#;', ' ')
                # Remove non-word characters
                document = re.sub('\W', ' ', document)
                # Remove digits
                document = re.sub(r'\d+', ' ', document)
                # Normalize each document to lower case and strip the leading and trailing spaces
                document = document.lower().strip()
                # No need for the id now
                documents.append(document)
    return documents


# This method tokenize the documents and construct an positional inverted index.
def tokenize(documents):
    # Read the stopwords
    stop_word_set = set(open('./stopwords.txt', 'r').read().split())
    # Initialize the Porter stemmer
    p = PorterStemmer()
    # Create a dictionary where each element is also a dictionary. The outer dictionary will map stemmed words to
    # document ids and the inner dictionaries will map the document ids to their indices in the document.
    word_to_doc = defaultdict(lambda: defaultdict(list))  # Positional inverted index
    for article_index, document in enumerate(documents, start=1):
        for word_index, word in enumerate(document.split()):
            if word not in stop_word_set:
                # Store each word as stemmed and put them to the inverted index
                stemmed_word = p.stem(word, 0, len(word) - 1)
                word_to_doc[stemmed_word][article_index].append(word_index)

    return word_to_doc


# This method maps each word to an id and creates postings lists based on these ids.
def create_index_files(word_to_doc):
    # Create word to id mapping
    word_to_index = {word: index for index, word in enumerate(list(word_to_doc.keys()))}
    # Create word to postings lists
    postings_lists = {word_to_index[word]: word_to_doc[word] for word in word_to_doc.keys()}
    # Dump these files for future use as pickle files.
    pickle.dump(word_to_index, open('word_to_index.pkl', 'wb'))
    pickle.dump(postings_lists, open('postings_lists.pkl', 'wb'))


def main():
    # First extract each document to index, tokenize them and create index files.
    documents = extract_documents()
    word_to_doc = tokenize(documents)
    create_index_files(word_to_doc)


if __name__ == "__main__":
    main()
