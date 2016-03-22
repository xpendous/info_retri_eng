__author__ = 'viva'

import codecs
import math
import os
import re
from collections import defaultdict
from time import clock


class CreateInvertedIndex:

    def __init__(self):
        self.invertedIndex = defaultdict(list)
        self.tf = defaultdict(list)
        self.df = defaultdict(int)
        self.numBlogs = 0

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

    def parseBlog(self, blogs, blogname):
        blog = []
        dic = {}
        for line in blogs:
            if line != '\n':
                blog.append(line)
        blog = ''.join(blog)
        dic['blogid'] = blogname.split('.')[0]
        dic['blogtext'] = blog

        return dic

    def writeInvertedIndexToFile(self):
        file = open('invertedIndexFile.dat', 'w')
        print >> file, self.numBlogs    # first line of the file is the number of blogs
        for word in self.invertedIndex.iterkeys():
            postings = []
            for post in self.invertedIndex[word]:
                blogid = post[0]
                positions = post[1]
                postings.append(':'.join([blogid, ','.join(map(str, positions))]))

            # print data to file
            postingData = ';'.join(postings)
            tfData = ','.join(map(str, self.tf[word]))
            idfData = '%.5f' % math.log(float(self.numBlogs)/self.df[word], 2)
            print >> file, '$'.join((word, tfData, idfData, postingData))
        file.close()

    def createInvertedIndex(self):
        # main program, that is to construct the inverted index
        self.getStopWords()
        files = os.listdir('blogs')

        for fname in files:
            self.numBlogs += 1

            blog = codecs.open('blogs' + '/' + fname, 'r', 'utf-8')     # open blog file
            blogdic = self.parseBlog(blog, fname)    # parse the blog to get the blog text and id

            blogid = blogdic['blogid']
            words = self.getWords(blogdic['blogtext'])

            # build the index for current blog file
            worddic = {}
            try:
                for pos, word in enumerate(words):
                    try:
                        worddic[word][1].append(pos)
                    except:
                        worddic[word] = [blogid, [pos]]

                # normalization
                norm = 0
                for word, posting in worddic.iteritems():
                    norm += len(posting[1])**2
                norm = math.sqrt(norm)

                # calculate the tf-idf weights
                for word, posting in worddic.iteritems():
                    self.tf[word].append('%.5f' % (len(posting[1])/norm))
                    self.df[word] += 1

                # merge dictionary for all blog files
                for word, posting in worddic.iteritems():
                    self.invertedIndex[word].append(posting)

            finally:
                blog.close()

        self.writeInvertedIndexToFile()

if __name__ == "__main__":
    start = clock()
    create = CreateInvertedIndex()
    create.createInvertedIndex()
    finish = clock()
    print ("Indexing time: " + str(finish - start) + " seconds.")