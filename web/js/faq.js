$(document).ready(function(){
	$("#faq_overview").append('<p>FAQ</p>')
	$("h1, h2, h3").each(function(i) { // jQuery multiple-selector
		var current = $(this);
		current.attr("id", "title" + i);
		$("#toc").append("<a id='link" + i + "' href='#title" +
			i + "' title='" + current.attr("tagName") + "'>" + 
			current.html() + "</a>");
	});
})


