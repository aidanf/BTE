#!/usr/bin/python

import htmllib
import formatter
import string 
import sys,urllib

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
	def __init__(self):
		HtmlTokenParser.__init__(self)
		self.encoded = [0]
		self.lookup0N = [0]
		self.lookupN0 = [0]		
		self.body_txt = ""
	
	def close(self):
		HtmlTokenParser.close(self)
		self._encode_binary_tokens()
		self._initialise_lookups()

	def _encode_binary_tokens(self):
		i = 0
		for x in self.binary_tokens:
			if(abs(x + self.encoded[i]) < abs(self.encoded[i])):
				i = i + 1
				self.encoded.append(0)
			self.encoded[i] = self.encoded[i] + x			

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
		
	def _objective_fcn(self,i,j):
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
	
	def body_text(self):
		obj_max = 0
		i_max = 0
		j_max = len(self.encoded)-1
		for i in range(len(self.encoded)-1):
			for j in range(i,len(self.encoded)):
				obj = self._objective_fcn(i,j)
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

	def full_text(self):
		ft = ""
		for x in self.tokens[0:-1]:
			if(not(self._is_tag(x))):
				ft = ft + x + " "
		return ft

if __name__ == '__main__':
	html = open(sys.argv[1]).read()
	p = HtmlBodyTextExtractor()
	p.feed(html)
	p.close()
	x = p.body_text()
	s = p.summary()
	t = p.full_text()
	print "\n\nSummary:\n",s
	print "\nBodytext:\n",x
	print "\nFulltext:\n",t

# (c) 2001 Aidan Finn
# Released under the terms of the GNU GPL





