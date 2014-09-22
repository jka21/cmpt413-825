
import sys, codecs, optparse, os, heapq

optparser = optparse.OptionParser()
optparser.add_option("-c", "--unigramcounts", dest='counts1w', default=os.path.join('data', 'count_1w.txt'), help="unigram counts")
optparser.add_option("-b", "--bigramcounts", dest='counts2w', default=os.path.join('data', 'count_2w.txt'), help="bigram counts")
optparser.add_option("-i", "--inputfile", dest="input", default=os.path.join('data', 'input'), help="input file to segment")
(opts, _) = optparser.parse_args()

class Pdist(dict):
	"A probability distribution estimated from counts in datafile."
	def __init__(self, filename, sep='\t', N=None, missingfn=None):
		for line in file(filename):		
			(key,count) = line.split(sep)
			key = key.decode('utf-8')
			self[key] = self.get(key, 0) + int(count)			
		self.N = float(sum(self.itervalues()))
		self.missingfn = (lambda k, N: 1./(N*math.exp(len(k))))
	def __call__(self, key):
		if key in self: return self[key]/self.N
		else: return self.missingfn(key, self.N)

class Pdist2(dict):
	"A probability distribution estimated from counts in datafile."
	def __init__(self, filename, sep='\t', N=None, missingfn=None):
	        self.maxlen = 0 
		self.N = 0
	        for line in file(filename):
			(key, freq) = line.split(sep)
			try:
				utf8key = unicode(key, 'utf-8')
			except:
				raise ValueError("Unexpected error %s" % (sys.exc_info()[0]))
		
			spacePos = utf8key.find(' ')
			utf8key = utf8key.strip().replace(" ", "")
			self[utf8key] = self.get(utf8key, {})
			self[utf8key][spacePos] = int(freq)
			self.N += int(freq)

			self.maxlen = max(len(utf8key), self.maxlen)
	        #self.N = float(N or sum(self.itervalues()))
	        self.missingfn = missingfn or (lambda k, N: 1./N)
	
	def __call__(self, key):
		spacePos = key.find(' ')
		key = key.strip().replace(" ", "")
        	if key in self: return float(self[key][spacePos])/float(self.N)
        	#else: return self.missingfn(key, self.N)
        	else: return self.missingfn(key, self.N)
        	#else: return None

# the default segmenter does not use any probabilities, but you could ...
Pw2 = Pdist2(opts.counts2w)
Pw = Pdist(opts.counts1w)

old = sys.stdout
sys.stdout = codecs.lookup('utf-8')[-1](sys.stdout)
# ignoring the dictionary provided in opts.counts

from numpy import *
class Entry():
	def __init__(self, word, logP):
		self.word = word
		self.logP = logP
		self.startPos = 0
		self.backPointer = None
	def __init__(self, word, startPos, logP, backPointer):
		self.word = word
		self.startPos = startPos
		self.logP = logP
		self.backPointer = backPointer
	def __eq__(self, comp):
		return self.word == comp.word and self.startPos == comp.startPos

with open(opts.input) as f:	
	for line in f:
		utf8line = unicode(line.strip(), 'utf-8')		# a line read from input file
		line_length = len(utf8line)				# length of read line
		chart = {}						# the chart to store best solutions
		heap = []						# the heap
		matched_words = [[] for n in range(0, line_length)]	# list of all words from Pw that match input line at all possible positions
									# matched_words[i] is the list of all words from Pw that match input line at position i

		# Build matched_word_position list
		for i in range(0, line_length):
			for j in range(i+1, line_length+1):
				if utf8line[i:j] in Pw:
					dict = Pw[utf8line[i:j]]
					for spacePos in dict:
						word = utf8line[i:j][0:spacePos] + ' ' + utf8line[i:j][spacePos:]
						print word
						matched_words[i].append(word)

sys.stdout = old
