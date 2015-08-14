//consider this: 
	// setTimeout(GetProgress(), 2000);

function getSnpsnapScore(sid) {
	//alert("getSnpsnapScore() is called");
	$.ajax({
		url:"app/report_snpsnap_score_html.py",
		type: 'POST',
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
		type: 'POST',
		data: {session_id:sid}, 
		dataType: "html",
		success: function(res){
			$("#collapse_input_to_matched_ratio .panel-body").html(res);
		}
	})
}



function getClump(sid) {
	$.ajax({
		url:"app/report_clump.py",
		type: 'POST',
		data: {session_id:sid}, 
		dataType: "html",
		success: function(res){
			$("#collapse_input_loci_independence .panel-body").html(res);
		}
	})
}


$(document).ready(function(){
	// Get hidden parameters
	var sid = $('#session_id').val();
	var set_file = $('#set_file').val()
	var annotate = $('#annotate').val()
	var clump = $('#clump').val()
	
	// TOGGLE: progress bars
	//Boolean(set_file) gives 'false' or 'true' in python
	$('#row_progress_set_file').toggle( Boolean(set_file) );
	$('#row_progress_annotate').toggle( Boolean(annotate) );
	$('#row_progress_clump').toggle( Boolean(clump) );

	// HIDE: panels (report and results)
	$('#panel_snpsnap_score').hide();
	$('#panel_input_to_matched_ratio').hide();
	$('#panel_input_loci_independence').hide(); //NEW
	$('#panel_results').hide();

	// FOR DEBUGGING
	//console.log( "set_file is: *" + set_file + "*" )
	//console.log( "annotate is: *" + annotate + "*" )
	//var data_parse_cgi = {key1: 'value1', key2: 'value2'}
	var data_parse_cgi = {session_id:sid, set_file:set_file, annotate:annotate, clump:clump}
	if (true) {
		
		// The below "flags" will be set to false when their respective function has been called.
		// This is to avoid making unnecessary ajax calls
		var call_getSnpsnapScore = true;
		var call_getInputToMatchedRatio = true;
		var call_getClump = true;

		var progresspump = setInterval(function(){
		
		$.ajax({
			url:"app/parse_returncode.py",
			type: 'POST',
			data: data_parse_cgi, // only the session_id is used
			dataType: "json",
			success: function(res){
				if (res.dummy == 0) { // if dummy == 0 then we know that the XXX_returncodes.json file is written and ALL return codes are available.
					var failure = false
					if (res.hasOwnProperty('match') && res.match != 0) { // If 'match' fails, then set_file and bias calculation has also failed (they are computed in the same call)
						// MATCH
						$("#progress_bar_match").hide();
						$("#row_progress_match .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
						$("#row_progress_match .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
						// SET_FILE
						$("#progress_bar_set_file").hide();
						$("#row_progress_set_file .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
						$("#row_progress_set_file .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
						// BIAS
						$("#progress_bar_bias").hide();
						$("#row_progress_bias .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
						$("#row_progress_bias .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
						// setting failure flag
						failure = true
					}
					if (res.hasOwnProperty('annotate') && res.annotate != 0) {
						//ANNOTATE
						$("#progress_bar_annotate").hide();
						$("#row_progress_annotate .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
						$("#row_progress_annotate .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
						// setting failure flag
						failure = true
					}
					if (res.hasOwnProperty('clump') && res.clump != 0) {
						//CLUMP
						$("#progress_bar_clump").hide();
						$("#row_progress_clump .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
						$("#row_progress_clump .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
						// setting failure flag
						failure = true
					}
					if (failure) {
						$("#collapse_progress .panel-body").append("<p class='text-danger text-center'>We are sorry, but one or more of your jobs could not be completed due to internal error.<br>Please re-run the job and report to the SNPsnap team if you keep getting this error message.</p>")
					}

					clearInterval(progresspump); // STOP all ajax calls. 
				}
			}
		})

		/////////////// BEFORE 09/15/2014 /////////////////
		//////// Things 'wrong': 
			// 1) Calculating match bias were still listed as 'Complete' even though an error occured
			// 2) parsing too simple (txt). did not allow for specific fails
			// 3) Not message about how to treat this error
		// $.ajax({
		// 	url:"app/parse_returncode.py",
		// 	type: 'POST',
		// 	data: data_parse_cgi, // only the session_id is used
		// 	dataType: "text",
		// 	success: function(res){
		// 		var returncode = Number(res)
		// 		// console.log(returncode)
		// 		// console.log(typeof returncode)
		// 		if (returncode != 0) {
		// 			// MATCH
		// 			$("#progress_bar_match").hide();
		// 			$("#row_progress_match .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
		// 			$("#row_progress_match .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
		// 			// SET_FILE
		// 			$("#progress_bar_set_file").hide();
		// 			$("#row_progress_set_file .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
		// 			$("#row_progress_set_file .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
		// 			//ANNOTATE
		// 			$("#progress_bar_annotate").hide();
		// 			$("#row_progress_annotate .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
		// 			$("#row_progress_annotate .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");
		// 			//CLUMP
		// 			$("#progress_bar_clump").hide();
		// 			$("#row_progress_clump .text-info").removeClass('text-info').addClass('text-danger').html('ERROR');
		// 			$("#row_progress_clump .error_description").append( "<p class=text-danger>Job could not be completed due to internal error</p>");

		// 			clearInterval(progresspump); // STOP all ajax calls
		// 		}
		// 	}
		// })
		$.ajax({
			url:"app/status_json.py",
			type: 'POST', 
			data: data_parse_cgi, 
			dataType: "json",
			success: function(res){
				if (res.error.error_status) { // true
					$("#row_progress_match").hide();
					$("#row_progress_set_file").hide();
					$("#row_progress_bias").hide();
					$("#row_progress_annotate").hide();
					$("#row_progress_clump").hide();
					
					//$("#collapse_progress .panel-body").append("<p class='text-danger text-center'>I am sorry, but we could not find any of your SNPs in the SNPsnap database.</p>")
					$("#collapse_progress .panel-body").append("<p class='text-danger text-center'>Input problem:" + res.error.error_msg + "</p>")
					clearInterval(progresspump);

				}
				

				$("#progress_bar_match .progress-bar").css('width', res.match.pct_complete+'%');
				$("#progress_bar_match .progress-bar").html(res.match.pct_complete + "%");
				$("#row_progress_match .text-info").html(res.match.status);
				if (res.match.status == 'finalizing' && call_getSnpsnapScore) { // snpsnap_query.py few_matches_report() has finished. json file can be read [but not completely finished] to get score.
					$('#row_progress_bias').show();
					$('#panel_snpsnap_score').show(); // new 09/11/2014
					getSnpsnapScore(sid); // new 09/11/2014
					call_getSnpsnapScore = false;
				} else if (res.match.status == 'complete') {
					$("#progress_bar_match").removeClass('active')
				}
				// Update the bias calculation
				// TODO: consider being more cautionate about trying to set these properties - they might cause an expection and the script to crash 
				$("#progress_bar_bias .progress-bar").css('width', res.bias.pct_complete+'%');
				$("#progress_bar_bias .progress-bar").html(res.bias.pct_complete + "%");
				$("#row_progress_bias .text-info").html(res.bias.status);
				if (res.bias.status == 'complete' && call_getInputToMatchedRatio) {
					$("#progress_bar_bias").removeClass('active');
					$('#panel_input_to_matched_ratio').show(); // new 09/11/2014
					getInputToMatchedRatio(sid); // new 09/11/2014
					call_getInputToMatchedRatio = false;
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

				if (clump) {
					$("#progress_bar_clump .progress-bar").css('width', res.clump.pct_complete+'%');
					$("#progress_bar_clump .progress-bar").html(res.clump.pct_complete + "%");
					$("#row_progress_clump .text-info").html(res.clump.status);
					if (res.clump.status == 'complete' && call_getClump) {
						$("#progress_bar_clump").removeClass('active')
						$('#panel_input_loci_independence').show();
						getClump(sid);
						call_getClump = false;
					}
				}

				// If everything is cleared: stop making .ajax calls to status_json.py
				if (res.status_all_complete) {
					clearInterval(progresspump);
					$('#panel_results').show();

					// BEFORE 09/11/2014
					// $('#panel_snpsnap_score').show();
					// $('#panel_input_to_matched_ratio').show();
					// $('#panel_results').show();
					// getSnpsnapScore(sid);
					// getInputToMatchedRatio(sid);
				}
			}
		})
		}, 2000)
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



