import bisect
import pickle

from PorterStemmer import PorterStemmer


# This method is responsible for searching related documents given a proximity query. Note that proximity value -1 is
# set as a special marker and it will be used for type 1 query. All of the type 2 queries are converted to type 3 by
# adding 0 as proximity.
def retrieve_documents(word_to_index, postings_lists, query_tokens):
    # Initialize a Porter stemmer for the stemming operations
    p = PorterStemmer()
    # Store keywords and proximities in two different lists. Note that each query type was converted to type3 query
    # prior to calling of this method. Thus, there would be no compatibility problem
    keywords, proximities = [], []
    for i in range(len(query_tokens)):
        if i % 2 == 0:
            keywords.append(p.stem(query_tokens[i], 0, len(query_tokens[i]) - 1))
        else:
            proximities.append(int(query_tokens[i][1:]))
    # Retrieve documents where each is token is found at least once
    doc_lists = [set(postings_lists[word_to_index[keyword]].keys()) for keyword in keywords]
    # Intersect these documents to construct the common document set. Thanks to this intersection, answers to type 1
    # query is ready and search space for type 3 query is reduced. Note that type 2 query is a special case of type 3
    # query.
    common_documents = set.intersection(*doc_lists)
    # Return the answer for type 1 query
    if proximities[0] == -1:
        return sorted(common_documents)
    # Now start the search for type 3 query. The algorithm is as follows: Iterate through each document in the common
    # document list and for each token, check if matches the condition with the adjacent token. If so, move to the next
    # token. It is similar to sliding a search window over tokens for each document.
    matched_documents = []
    for doc in common_documents:
        # Obtain the first token and its postings list
        token_1 = keywords[0]
        index_of_token_1 = word_to_index[token_1]
        token_1_postings_list = postings_lists[index_of_token_1][doc]
        for keyword_index in range(1, len(keywords)):
            # Obtain the corresponding proximity value.
            proximity = proximities[keyword_index - 1]
            # Obtain the second token and its postings list
            token_2 = keywords[keyword_index]
            index_of_token_2 = word_to_index[token_2]
            token_2_postings_list = postings_lists[index_of_token_2][doc]
            frequency_of_token2 = len(token_2_postings_list)
            match_indices = [] # This list will store the indices that satisfy the proximity condition
            for index1 in token_1_postings_list:
                # Find the ordinal of the index1 in the second token's posting list
                ordinal_in_list2 = bisect.bisect_left(token_2_postings_list, index1)
                # If the ordinal equal to length of the list, break the loop, since this means that it is larger than
                # any index in the postings list
                if ordinal_in_list2 == frequency_of_token2:
                    break
                # If the condition satisfied, than add this index to matched indices
                if token_2_postings_list[ordinal_in_list2] <= index1 + proximity + 1:
                    match_indices.append(token_2_postings_list[ordinal_in_list2])
            # Now slide the window.To do so, set the index list of next token to match indices. This way, the algorithm
            # would never break the satisfied conditions
            token_1_postings_list = match_indices[:]
            # If there is no match, just break the loop
            if len(match_indices) == 0:
                break
        # If the document succeded to move indices to the end, add it to the matched documents,
        if len(token_1_postings_list) > 0:
            matched_documents.append(doc)
    # Return the matched documents in sorted order.
    return sorted(matched_documents)


def main():
    # Read index files to variables.
    word_to_index = pickle.load(open('word_to_index.pkl', 'rb'))
    postings_lists = pickle.load(open('postings_lists.pkl', 'rb'))
    # Take input from the user.
    query = input()
    # For entering query inside the program please uncomment this line.
    # query = '3  common /0 stock /0 under'
    # Parse the query type
    query_tokens = query.split()
    query_type = int(query_tokens.pop(0))
    # Normalize each query type by changing their form to the form of query 3.This will remove the necessity of separate
    # functions for each query type.
    if query_type == 1:
        # Replace each AND with -1 since no proximity is required in this case. It will be treated as a special case.
        query_tokens = [token if token != 'AND' else '/-1' for token in query_tokens]
    elif query_type == 2:
        # Add 0s as proximity values
        modified_tokens = []
        for token in query_tokens:
            modified_tokens.append(token)
            modified_tokens.append('/0')
        modified_tokens.pop()
        query_tokens = modified_tokens[:]
    # Now call the search method.
    matched_documents = retrieve_documents(word_to_index, postings_lists, query_tokens)
    print(matched_documents)

if __name__ == '__main__':
    main()
