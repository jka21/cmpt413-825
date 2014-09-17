import sys, codecs, optparse, os, heapq

optparser = optparse.OptionParser()
optparser.add_option("-c", "--unigramcounts", dest='counts1w', default=os.path.join('data', 'count_1w.txt'), help="unigram counts")
optparser.add_option("-b", "--bigramcounts", dest='counts2w', default=os.path.join('data', 'count_2w.txt'), help="bigram counts")
optparser.add_option("-i", "--inputfile", dest="input", default=os.path.join('data', 'input'), help="input file to segment")
(opts, _) = optparser.parse_args()

class Pdist(dict):
	"A probability distribution estimated from counts in datafile."
	def __init__(self, data=[]):
		for key,count in data:
			key = key.decode('utf-8')
			self[key] = self.get(key, 0) + int(count)			
		self.N = float(sum(self.itervalues()))
		self.missingfn = (lambda k, N: 1./N)
	def __call__(self, key):
		if key in self: return self[key]/self.N
		else: return self.missingfn(key, self.N)

def datafile(name, sep='\t'):
    "Read key,value pairs from file."
    for line in file(name):
        yield line.split(sep)

# the default segmenter does not use any probabilities, but you could ...
Pw  = Pdist(datafile(opts.counts1w))

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
		utf8line = unicode(line.strip(), 'utf-8')					# a line read from input file
		line_length = len(utf8line)									# length of read line
		chart = {}													# the chart to store best solutions
		heap = []													# the heap
		matched_words = [n for n in range(0, line_length)]				# list of all words from Pw that match input line at all possible positions
																	# matched_words[i] is the list of all words from Pw that matche input line at position i
		
		# Build matched_word_position list
		for i in range(0, line_length):
			matched_words[i] = []
			for word in Pw:
				if utf8line.find(word,i) == i:
					matched_words[i].append(word)
			
		# Initialize the heap		
		for word in matched_words[0]:
			"For every word in Pw that matches input at position 0, create a new entry and push it into the heap"
			entry = Entry(word,0, log(Pw(word)),None)
			heapq.heappush(heap, (0, entry))
		if len(matched_words[0]) == 0:
			"If there's no word matches input at position 0 - consider the first character is a word, create a new entry and push it into the heap"
			entry = Entry(utf8line[0], 0, log(Pw(utf8line[0])), None)
			heapq.heappush(heap, (0, entry))
				
		# Iteratively fill in chart[i] for all i
		while(len(heap)):
			entry = heapq.heappop(heap)[1]										# Pop the first entry in the heap
			endindex = entry.startPos + len(entry.word)							# Compute the "endindex" value: the position to be considered for the next segmentation
			preventry = chart[endindex] if chart.has_key(endindex) else None	# Check if there is already a known segmentation at this position
			if preventry != None:
				if (preventry.logP <= entry.logP):								# If the "preventry" (known segmentation) has lower probability than the new one
					chart[endindex] = entry										# update the chart (stores the known best solution) with the new segmentation
				else: continue
			else:
				chart[endindex] = entry									# or if there is no "preventry", update the current segmentation as the known best solution

			# Find the next segmentation from the "endindex" position
			if endindex >= line_length:
				continue;				# if we reached the end of the input line, just continue...
			
			if len(matched_words[endindex]) > 0:
				# If we found a newword that matches input at position "endindex" and it's not in the heap yet, then push it into the heap
				for newword in matched_words[endindex]:										
					newentry = Entry(newword, endindex, entry.logP + log(Pw(newword)), entry)
					if (endindex, newentry) not in heap:
						heapq.heappush(heap, (endindex, newentry))
			else:
				# else, consider the next character is a word, then push it into the heap"
				newentry = Entry(utf8line[endindex], endindex, log(Pw(utf8line[endindex])), entry)
				if (endindex, newentry) not in heap:
					heapq.heappush(heap, (endindex, newentry))
	
		# Get the best segmentation			
		finalindex = len(utf8line)
		finalentry = chart[finalindex]
		index = []
		while finalentry != None:
			"Trace back the solution by backPointer"
			index.insert(0,[finalentry.startPos, len(finalentry.word)])			
			finalentry = finalentry.backPointer
		
		output = splits=[utf8line[i[0]:i[0]+i[1]] for i in index]
		print " ".join(output)
sys.stdout = old
