import sys,BodyTextExtractor

# Usage: python example.py html_file

html = open(sys.argv[1]).read()
p = BodyTextExtractor.HtmlBodyTextExtractor()
p.feed(html)
p.close()
x = p.body_text()
s = p.summary()
t = p.full_text()
print "\n\nSummary:\n",s
print "\nBodytext:\n",x
print "\nFulltext:\n",t
