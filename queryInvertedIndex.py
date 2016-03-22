__author__ = 'viva'
import copy
import re
import sys
from collections import defaultdict


class QueryInvertedIndex:

    def __init__(self):
        self.invertedIndex = {}
        self.tf = {}
        self.idf = {}
        self.topRanks = 100

    def getWords(self, texts):
        texts = texts.lower()
        texts = re.sub(r'[^a-z0-9 ]', ' ', texts)
        words = texts.split()
        words = [word for word in words if word not in self.sw]

        return words

    def getStopWords(self):
        swFile = open('stopwords.dat', 'r')
        stopwords = [line.rstrip() for line in swFile]
        self.sw = dict.fromkeys(stopwords)
        swFile.close()

    def getPostings(self, words):
        return [self.invertedIndex[word] for word in words]

    def getBlogsFromPostings(self, postings):
        return [[post[0] for post in posting] for posting in postings]

    def intersection(self, lists):
        if len(lists) == 0:
            return []
        lists.sort(key=len)
        return list(reduce(lambda x, y: set(x) & set(y), lists))

    def dotProduct(self, vector1, vector2):
        if len(vector1) != len(vector2):
            return 0
        return sum([x * y for x, y in zip(vector1, vector2)])

    def rankBlogs(self, words, blogs):
        blogVectors = defaultdict(lambda: len(words)*[0])
        queryVector = len(words)*[0]
        for wordIndex, word in enumerate(words):
            #if word not in self.invertedIndex:
            #   continue
            queryVector[wordIndex] = self.idf[word]
            for blogIndex, (blog, postings) in enumerate(self.invertedIndex[word]):
                if blog in blogs:
                    blogVectors[blog][wordIndex] = self.tf[word][blogIndex]

        # calculate the scores for each blog
        scores = [[self.dotProduct(blogVector, queryVector), blog] for blog, blogVector in blogVectors.iteritems()]
        scores.sort(reverse=True)
        if len(param) == 1:
            return [score[1] for score in scores][:self.topRanks]

        else:
            return [score[1] for score in scores]

    def readInvertedIndexFromFile(self):
        file = open('invertedIndexFile.dat', 'r')
        file.readline().rstrip()        # first line is the number of blog, remove it!
        for line in file:
            line = line.rstrip()
            word, tf, idf, postings = line.split('$')

            # read postings
            postings = postings.split(';')
            postings = [posting.split(':') for posting in postings]
            postings = [[posting[0], map(int, posting[1].split(','))] for posting in postings]
            self.invertedIndex[word] = postings

            # read tf-idf weights
            tf = tf.split(',')
            self.tf[word] = map(float, tf)
            self.idf[word] = float(idf)
        file.close

    def queryTypes(self, query):
        if '"' in query:
            return 'phraseQ'
        elif len(query.split()) > 1:
            return 'multiwordQ'
        elif len(query.split()) == 1:
            return 'onewordQ'

    def onewordQ(self, query):      # one word query
        query = self.getWords(query)
        if len(query) == 0:
            print 'your input is stop word'
            return
        word = query[0]
        if word not in self.invertedIndex:
           print 'no matching blog'
           return
        else:
            postings = self.invertedIndex[word]
            blogs = [posting[0] for posting in postings]
            rankedBlogs = self.rankBlogs(query, blogs)
            if len(param) == 1:
                print '\n'.join(rankedBlogs), '\n'
            else:
                return rankedBlogs


    def multiwordQ(self, query):        # multiword query
        query = self.getWords(query)
        if len(query) == 0:
            print 'your input are stop words'
            return
        elif len(query) == 1:
            self.onewordQ(query)
            return
        setBlogs = set()
        for word in query:
            if word not in self.invertedIndex:
                pass
            else:
                postings = self.invertedIndex[word]
                blogs = [posting[0] for posting in postings]
                setBlogs = setBlogs | set(blogs)

        listBlogs = list(setBlogs)
        rankedBlogs = self.rankBlogs(query, listBlogs)
        if len(param) == 1:
            print '\n'.join(rankedBlogs), '\n'
        else:
            return rankedBlogs

    def phraseQ(self, query):       # phrase query
        query = self.getWords(query)
        if len(query) == 0:
            print 'your input are stop words'
            return
        elif len(query) == 1:
            self.onewordQ(query)
            return
        phraseBlogs = self.phraseQBlogs(query)
        rankedBlogs = self.rankBlogs(query, phraseBlogs)
        if len(param) == 1:
            print '\n'.join(rankedBlogs), '\n'
        else:
            return rankedBlogs

    def phraseQBlogs(self, query):
        phraseBlogs = []
        length = len(query)
        for word in query:
            if word not in self.invertedIndex:  # only if one word not in index, no match
                return []
        postings = self.getPostings(query)
        blogs = self.getBlogsFromPostings(postings)
        blogs = self.intersection(blogs)        # every blog contains all words in query

        # filter the postings
        for i in xrange(len(postings)):
            postings[i] = [posting for posting in postings[i] if posting[0] in blogs]

        # check the words order in blog corresponding to the query
        postings = copy.deepcopy(postings)
        for i in xrange(len(postings)):
            for j in xrange(len(postings[i])):
                postings[i][j][1] = [x - i for x in postings[i][j][1]]

        # intersect the processed postings
        for i in xrange(len(postings[0])):
            lis = self.intersection([posting[i][1] for posting in postings])
            if lis == []:
                continue
            else:
                phraseBlogs.append(postings[0][i][0])
        return phraseBlogs

    def queryInvertedIndex(self):
        self.getStopWords()
        self.readInvertedIndexFromFile()
        while 1:
            print 'input the query(press enter to exit):'
            query = sys.stdin.readline()
            if query == '\n':
                break
            queryType = self.queryTypes(query)
            if queryType == 'phraseQ':
                self.phraseQ(query)
            elif queryType == 'multiwordQ':
                self.multiwordQ(query)
            elif queryType == 'onewordQ':
                self.onewordQ(query)
        print 'See you next time!'

    def autoEval(self):

        self.getStopWords()
        self.readInvertedIndexFromFile()
        qrelsFile = param[1]
        qrels = open(qrelsFile, 'r')
        qrelsDic = {}
        for qrel in qrels:
            qrel = re.sub(r'\n', '', qrel)
            qrel = qrel.split(' ')
            try:
                qrelsDic[qrel[0]][0].append(qrel[2])
                qrelsDic[qrel[0]][1].append(qrel[3])
            except:
                qrelsDic[qrel[0]] = [[qrel[2]], [qrel[3]]]

        topicsFile = param[2]
        topics = open(topicsFile, 'r')
        for topic in topics:
            topic = re.sub(r'\n', '', topic)
            topic = topic.split('\t')
            queryType = self.queryTypes(topic[1])

            if queryType == 'phraseQ':
                rankedBlogs = self.phraseQ(topic[1])
                if len(rankedBlogs) < self.topRanks:
                    rankedBlogs = self.multiwordQ(topic[1])
            elif queryType == 'multiwordQ':
                rankedBlogs = self.multiwordQ(topic[1])
            elif queryType == 'onewordQ':
                rankedBlogs = self.onewordQ(topic[1])

            qrelBlogs = qrelsDic[topic[0]][0]
            qrelValues = qrelsDic[topic[0]][1]
            vector = []
            sum = 0.0
            sumPrecision = 0.0
            for pos, rankedBlog in enumerate(rankedBlogs):
                if rankedBlog not in qrelBlogs:
                    vector.append([])
                else:
                    index = qrelBlogs.index(rankedBlog)
                    value = qrelValues[index]
                    if value == '0':
                        vector.append(0)
                    else:
                        sum += 1
                        sumPrecision += sum / (pos+1)
                        vector.append(1)
            # [retrieved, retrieved rel, retrieved irrel, total rel, average precision ]
            print len(rankedBlogs), vector.count(1), vector.count(0) + vector.count([]), \
                len(qrelValues)-qrelValues.count('0'),\
                sumPrecision/(len(qrelValues)-qrelValues.count('0'))

if __name__ == '__main__':
    param = sys.argv
    query = QueryInvertedIndex()
    if len(param) == 1:
        query.queryInvertedIndex()
    else:
        query.autoEval()