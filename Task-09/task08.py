import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from collections import Counter


def nltk_data():
    packs = {
        "punkt": "tokenizers/punkt",
        "stopwords": "corpora/stopwords",
        "punkt_tab": "tokenizers/punkt_tab",
    }

    for p, path in packs.items():
        try:
            nltk.data.find(path)
        except:
            nltk.download(p)
            


def run_nlp_task():
    nltk_data()

    text_data = """
    Myself Hamza Akmal and I'm 4th semester data science student at Superior University Lahore.
    Right now I'm doing the task 8 of PFA lab task which is umm based on NLP.
    """


text = text_data.lower() 
words = word_tokenize(text)

words_low = []
for w in words:
    if w.isalpha():
        words_low.append(w.lower())

# remove stopwords
stop_words = stopwords.words("english")
clean_words = []

for w in words_low:
    if w not in stop_words:
        clean_words.append(w)

# stemming
ps = PorterStemmer()
stem_words = []

for w in clean_words:
    stem_words.append(ps.stem(w))

# count words
counts = Counter(stem_words)

# get top 5
top_5 = counts.most_common(5)

print(top_5)

print("originl word count:", len(words))
print("After clean word count:", len(clean_words))



