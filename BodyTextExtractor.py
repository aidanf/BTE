#!/usr/bin/python

'''
Modified by Bill Bushey <wbushey@acm.org> and Brian Young <byoung061@gmail.com> on August 10th, 2009
'''

import htmllib
import formatter
import string 
import sys,urllib
import time

class HtmlTokenParser(htmllib.HTMLParser):
	# return a dictionary mapping anchor texts to lists
	# of associated hyperlinks     
	def __init__(self, verbose=0):
		self.tokens = []
		self.binary_tokens = []
		f = formatter.NullFormatter()
		htmllib.HTMLParser.__init__(self, f, verbose)     
	def unknown_tag(self):
		self.tokens.append("TAG")
		self.binary_tokens.append(1)
	def unknown_starttag(self,tag, attrs):
		self.tokens.append("<"+tag+">")
		self.binary_tokens.append(1)
	def unknown_endtag(self,tag):
		self.tokens.append("<\\"+tag+">")
		self.binary_tokens.append(1)
	def handle_data(self,data):
		for t in string.split(data):
			self.tokens.append(t)
			self.binary_tokens.append(-1)
	def handle_starttag(self,tag, method, attrs):
		self.binary_tokens.append(1)
		self.tokens.append("<"+tag+">")
	def handle_endtag(self,tag, method):
		self.tokens.append("<\\"+tag+">")
		self.binary_tokens.append(1)
		
class HtmlBodyTextExtractor(HtmlTokenParser):
	''' Modified to include the initialization of total_tokens_before'''
	def __init__(self):
		HtmlTokenParser.__init__(self)
		self.encoded = [0]
		self.total_tokens_before = [0]
		self.lookup0N = [0]
		self.lookupN0 = [0]
		self.body_txt = ""
	
	def close(self):
		HtmlTokenParser.close(self)
		self._encode_binary_tokens()
		self._initialise_lookups()

	''' Modified to set values in total_tokens_before'''
	def _encode_binary_tokens(self):
		i = 0
		for x in self.binary_tokens:
			if(abs(x + self.encoded[i]) < abs(self.encoded[i])):
				self.encoded.append(0)
				self.total_tokens_before.append(self.total_tokens_before[-1])
				i = i + 1
			self.encoded[i] = self.encoded[i] + x
			self.total_tokens_before[i] = self.total_tokens_before[i] + 1
		# total_tokens_before works better in the rest of the class if we shift all values up one index
		self.total_tokens_before.insert(0,0) 

	def _initialise_lookups(self):
		t = 0
		for x in self.encoded:
			if(x>0):
				t = t + x
			self.lookup0N.append(t)
		self.encoded.reverse()
		t = 0
		for x in self.encoded:
			if(x>0):
				t = t + x
			self.lookupN0.append(t)
		self.encoded.reverse()
		self.lookupN0.reverse()
		del(self.lookupN0[0]) #will never need these values
		del(self.lookup0N[-1])
		
	'''
	This method has been modified to be in O(1).
	This version of the method works with the assumption that all nodes are
	either text or tags. Since we can quickly find out the number of tags
	that have occured upto a given region, and the number of total tags up
	to that region, we can quickly calculate the number of text nodes that 
	have occured upto that region.

	The original method is available as _objective_fcn_old 
	'''
	def _objective_fcn(self,i,j):
		tags_to_i = self.lookup0N[i]
		tags_after_j = self.lookupN0[j]

		text_to_i = self.total_tokens_before[i] - tags_to_i
		text_to_j = self.total_tokens_before[j] - self.lookup0N[j]

		text_between_i_j = text_to_j - text_to_i
		return_val = tags_to_i + tags_after_j + text_between_i_j
		return return_val

	'''
	The original method, which is in O(n)
	'''
	def _objective_fcn_old(self,i,j):
		return_val = self.lookup0N[i] + self.lookupN0[j]
		for x in self.encoded[i:j]:
			if(x<0):
				return_val = return_val - x
		return return_val


	def _is_tag(self,s):
		if(s[0]=='<' and s[-1]=='>'):
			return(1)
		else:
			return(0)
	
	'''
	Method which uses the modified version of _objective_fcn, this function is in O(n^2)
	This method has also been modified to improve the finding of the 'start' and 'end' variables
	Finally, body_text now uses the join method for building the output string
	'''
	def body_text(self):
		self.body_txt = ""
		obj_max = 0
		i_max = 0
		j_max = len(self.encoded)-1
		for i in range(len(self.encoded)-1):
			if self.encoded[i] > 0:	
				continue
			for j in range(i,len(self.encoded)):
				if self.encoded[j] > 0:
					continue
				obj = self._objective_fcn(i,j)
				if(obj > obj_max):
					obj_max = obj
					i_max = i
					j_max = j
		start = self.total_tokens_before[i_max]
		end = self.total_tokens_before[j_max]

		self.body_txt = " ".join(x for x in self.tokens[start:end] if not self._is_tag(x))

		# This is added for testing purposes, so that the old and new versions produce the same string.
		self.body_txt = self.body_txt + " "

		return(self.body_txt)	

	'''
	Method which uses _objective_fcn_old, this function is in O(n^3)
	'''
	def body_text_old(self):
		self.body_txt = ""
		obj_max = 0
		i_max = 0
		j_max = len(self.encoded)-1
		for i in range(len(self.encoded)-1):
			for j in range(i,len(self.encoded)):
				obj = self._objective_fcn_old(i,j)
				if(obj > obj_max):
					obj_max = obj
					i_max = i
					j_max = j
		start = 0
		end = 0
		for x in self.encoded[:i_max]:
			start = start + abs(x)
		for x in self.encoded[j_max:]:
			end = end + abs(x)
		for x in self.tokens[start:-end]:
			if(not(self._is_tag(x))):
				self.body_txt = self.body_txt + x + " "
		return(self.body_txt)

	def summary(self, start=0, bytes=255):
		if(not(self.body_txt)):
			self.body_text()
		return(self.body_txt[start:(start+bytes)])

	'''
	Modified to use the more efficient join method for building the string
	'''
	def full_text(self):
		ft = ""
		ft = " ".join(x for x in self.tokens if not self._is_tag(x))
		return ft

if __name__ == '__main__':
	html = open(sys.argv[1]).read()
	t0 = time.clock()
	p = HtmlBodyTextExtractor()
	p.feed(html)
	p.close()
	r10 = range(10)
	t1 = time.clock()
	for r in r10:
		x = p.body_text()
	t2 = time.clock()
	for r in r10:
		z = p.body_text_old()
	t3 = time.clock()
	x = p.body_text()
	z = p.body_text_old()
	s = p.summary()
	t = p.full_text()
#	print "\nNew Bodytext:\n",x
#	print "\nOld Bodytext:\n",z
#	print "\nFull Text:\n",t
	if (x == z):
		print "The SAME!!!!!\n"
	print "Time to initialize: %f\nTime for new method: %f\nTime for old method: %f\n" % (t1-t0, t2-t1, t3-t2)

# (c) 2001 Aidan Finn
# Released under the terms of the GNU GPL





