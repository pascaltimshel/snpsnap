#!/usr/bin/python

# Import modules for CGI handling 
import cgi, cgitb 

cgitb.enable()

# Create instance of FieldStorage 
form = cgi.FieldStorage() 

# Get data from fields
if form.getvalue('maths'):
   math_flag = "ON"
else:
   math_flag = "OFF"

if form.getvalue('physics'):
   physics_flag = "ON"
else:
   physics_flag = "OFF"


text_entry = form.getvalue('textcontent', 'found nothing')

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers
print "<html>"
print "<head>"
print "<title>Hello - Second CGI Program</title>"
print "</head>"

print "<body>"
print "<h1>This is my first CGI script</h1>"
#print "Hello, world!"
print "<h6>By Pascal Timshel</h6>"


print "<p> Textarea is :</p>"
print """
<div, style="color:red;">
	%s
</div>
""" % cgi.escape(text_entry)



print "</body>"
print "</html>"



