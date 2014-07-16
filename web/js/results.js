//consider this: 
	// setTimeout(GetProgress(), 2000);

function getSnpsnapScore(sid) {
	//alert("getSnpsnapScore() is called");
	$.ajax({
		url:"app/report_snpsnap_score_html.py",
		data: {session_id:sid}, 
		dataType: "html",
		success: function(res){
			$("#collapse_snpsnap_score .panel-body").html(res);
		}
	})
}

function getInputToMatchedRatio(sid) {
	$.ajax({
		url:"app/report_input_to_matched_ratio_html.py",
		data: {session_id:sid}, 
		dataType: "html",
		success: function(res){
			$("#collapse_input_to_matched_ratio .panel-body").html(res);
		}
	})
}



$(document).ready(function(){
	// Get hidden parameters
	var sid = $('#session_id').val();
	var set_file = $('#set_file').val()
	var annotate = $('#annotate').val()
	
	// TOGGLE: progress bars
	//Boolean(set_file) gives 'false' or 'true' in python
	$('#row_progress_set_file').toggle( Boolean(set_file) );
	$('#row_progress_annotate').toggle( Boolean(annotate) );

	// HIDE: panels (report and results)
	$('#panel_snpsnap_score').hide();
	$('#panel_input_to_matched_ratio').hide();
	$('#panel_results').hide();

	// FOR DEBUGGING
	//console.log( "set_file is: *" + set_file + "*" )
	//console.log( "annotate is: *" + annotate + "*" )
	//var data_parse_cgi = {key1: 'value1', key2: 'value2'}
	var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate}
	if (true) {
		var progresspump = setInterval(function(){
		$.ajax({
			url:"app/parse_returncode.py",
			data: data_parse_cgi, // only the session_id is used
			dataType: "text",
			success: function(res){
				var returncode = Number(res)
				// console.log(returncode)
				// console.log(typeof returncode)
				if (returncode != 0) {
					// MATCH
					$("#progress_bar_match").hide();
					$("#row_progress_match .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
					$("#row_progress_match .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
					// SET_FILE
					$("#progress_bar_set_file").hide();
					$("#row_progress_set_file .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
					$("#row_progress_set_file .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
					//ANNOTATE					
					$("#progress_bar_annotate").hide();
					$("#row_progress_annotate .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
					$("#row_progress_annotate .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");

					clearInterval(progresspump); // STOP all ajax calls
				}
			}
		})
		$.ajax({
			url:"app/status_json.py",
			data: data_parse_cgi, 
			dataType: "json",
			success: function(res){

				$("#progress_bar_match .progress-bar").css('width', res.match.pct_complete+'%');
				$("#progress_bar_match .progress-bar").html(res.match.pct_complete + "%");
				$("#row_progress_match .text-info").html(res.match.status);
				if (res.match.status == 'finalizing') {
					$('#row_progress_bias').show();
				} else if (res.match.status == 'complete') {
					$("#progress_bar_match").removeClass('active')
				}
				// Update the bias calculation
				$("#progress_bar_bias .progress-bar").css('width', res.bias.pct_complete+'%');
				$("#progress_bar_bias .progress-bar").html(res.bias.pct_complete + "%");
				$("#row_progress_bias .text-info").html(res.bias.status);
				if (res.bias.status == 'complete') {
					$("#progress_bar_bias").removeClass('active')
				}

				if (set_file) {
					$("#progress_bar_set_file .progress-bar").css('width', res.set_file.pct_complete+'%');
					$("#progress_bar_set_file .progress-bar").html(res.set_file.pct_complete + "%");
					$("#row_progress_set_file .text-info").html(res.set_file.status);
					if (res.set_file.status == 'complete') {
						$("#progress_bar_set_file").removeClass('active')
					}
				}

				if (annotate) {
					$("#progress_bar_annotate .progress-bar").css('width', res.annotate.pct_complete+'%');
					$("#progress_bar_annotate .progress-bar").html(res.annotate.pct_complete + "%");
					$("#row_progress_annotate .text-info").html(res.annotate.status);
					if (res.annotate.status == 'complete') {
						$("#progress_bar_annotate").removeClass('active')
					}
				}
				// If everything is cleared: stop making .ajax calls to status_json.py
				if (res.status_all_complete) {
					clearInterval(progresspump);
					//$('#link_results').show();
					$('#panel_snpsnap_score').show();
					$('#panel_input_to_matched_ratio').show();
					$('#panel_results').show();
					getSnpsnapScore(sid);
					getInputToMatchedRatio(sid);
				}
			}
		})
		}, 1000)
	}
 })




















// WORKS WITH BOOT STRAP Version 2.3 - OLD PROGRESS BAR TYPE

// $(document).ready(function(){
// 	var sid = $('#session_id').val();
// 	//alert("function called: "+ sid)
	
// 	var set_file = $('#set_file').val() // gives 'false' or 'true'
// 	var annotate = $('#annotate').val() // gives 'false' or 'true'
// 	// var set_file = Boolean($('#set_file').val()) // gives 'false' or 'true'
// 	// var annotate = Boolean($('#annotate').val()) // gives 'false' or 'true'
// 	$('#progress_bar_set_file').toggle( Boolean(set_file) );
// 	$('#progress_bar_annotate').toggle( Boolean(annotate) );


// 	console.log( "set_file is: *" + set_file + "*" )
// 	console.log( "annotate is: *" + annotate + "*" )
// 	//var data_parse_cgi = {key1: 'value1', key2: 'value2'}
// 	//var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate}
// 	var job_complete = false
// 	var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate}
// 	//consider this: setTimeout(GetProgress(), 2000);
// 	if (true) {
// 		var progresspump = setInterval(function(){
// 		$.ajax({
// 			url:"/app/status_json.py",
// 			//data: "session_id="+sid,
// 			data: data_parse_cgi, 
// 			dataType: "json",
// 			success: function(res){
// 				//var data = $.parseJSON(response.d);
// 				//alert("succes")
// 				//alert(response)
// 				//$("#progress").css('width',res.match.pct_complete+'%');
// 				//console.log( "res.match.pct_complete: *" + res.match.pct_complete + "*" )
// 				// #progress_bar_match .progress.progress-striped.active .bar
// 				$("#progress_bar_match .progress.progress-striped.active .bar").css('width', res.match.pct_complete+'%');
// 				$("#progress_bar_match .progress.progress-striped.active .bar").html(res.match.pct_complete + "% | " + res.match.status );
// 				// $("#tmp").css('width', res.match.pct_complete+'%');
// 				// $("#tmp").html(res.match.pct_complete + "% | " + res.match.status );
// 				if (set_file) {
// 					$("#progress_bar_set_file progress").val(res.set_file.pct_complete);
// 					$("#status_pct_set_file").html(res.set_file.pct_complete + "% | " + res.set_file.status );
// 				}
// 				if (annotate) {
// 					$("#progress_bar_annotate progress").val(res.annotate.pct_complete);
// 					$("#status_pct_annotate").html(res.annotate.pct_complete + "% | " + res.annotate.status );
// 				}
// 				console.log( "res.status_all_complete is: *" + res.status_all_complete + "*" )
// 				if (res.status_all_complete) {
// 					clearInterval(progresspump);
// 					$('#link_results').show();
// 				}
// 			}
// 		})
// 		}, 1000)
// 	}
//  })



