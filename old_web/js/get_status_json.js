$(document).ready(function(){
	var sid = $('#session_id').val();
	//alert("function called: "+ sid)
	
	var set_file = $('#set_file').val() // gives 'false' or 'true'
	var annotate = $('#annotate').val() // gives 'false' or 'true'
	// var set_file = Boolean($('#set_file').val()) // gives 'false' or 'true'
	// var annotate = Boolean($('#annotate').val()) // gives 'false' or 'true'
	$('#progress_bar_set_file').toggle( Boolean(set_file) );
	$('#progress_bar_annotate').toggle( Boolean(annotate) );


	console.log( "set_file is: *" + set_file + "*" )
	console.log( "annotate is: *" + annotate + "*" )
	//var data_parse_cgi = {key1: 'value1', key2: 'value2'}
	//var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate}
	var job_complete = false
	var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate}
	//consider this: setTimeout(GetProgress(), 2000);
	if (true) {
		var progresspump = setInterval(function(){
		$.ajax({
			url:"/app/status_json.py",
			//data: "session_id="+sid,
			data: data_parse_cgi, 
			dataType: "json",
			success: function(res){
				//var data = $.parseJSON(response.d);
				//alert("succes")
				//alert(response)
				$("#progress_bar_match progress").val(res.match.pct_complete);
				$("#status_pct_match").html(res.match.pct_complete + "% | " + res.match.status );
				if (set_file) {
					$("#progress_bar_set_file progress").val(res.set_file.pct_complete);
					$("#status_pct_set_file").html(res.set_file.pct_complete + "% | " + res.set_file.status );
				}
				if (annotate) {
					$("#progress_bar_annotate progress").val(res.annotate.pct_complete);
					$("#status_pct_annotate").html(res.annotate.pct_complete + "% | " + res.annotate.status );
				}
				console.log( "res.status_all_complete is: *" + res.status_all_complete + "*" )
				if (res.status_all_complete) {
					clearInterval(progresspump);
					$('#link_results').show();
				}
			}
		})
		}, 1000)
	}
 })
