
function get_Snpsnap_Database_URL_and_Size(super_population, distance_type, distance_cutoff) {
	//alert("getSnpsnapScore() is called");
	$.ajax({
		url:"app/parse_snpsnap_database_info.py",
		type: 'POST',
		data: {super_population:super_population, distance_type:distance_type, distance_cutoff:distance_cutoff}, 
		// dataType: "html",
		dataType: "json",
		success: function(res){
			// var file = "/mpg/snpsnap/database/" + super_population + "/" + String(distance_type) + String(distance_cutoff) + "/" + String(distance_type) + String(distance_cutoff) + "_collection.tab";
			var file = "/mpg/snpsnap/database/" + super_population + "/" + String(distance_type) + String(distance_cutoff) + "/" + String(distance_type) + String(distance_cutoff) + "_collection.tab.gz";
			// e.g. /mpg/snpsnap/database/EUR/ld0.5/ld0.5_collection.tab.gz

			$("#q_super_population").html(res.super_population);
			$("#q_distance_type").html(res.distance_type);
			$("#q_distance_cutoff").html(res.distance_cutoff);
			$("#q_file_size").html(res.file_size);
			// $("#q_file").html(file);
			$("#q_file").attr('href', file); // Setting the href attribute (URL to file download)
		}
	})
}

function test() {
	console.log("returncode")
	alert("returncode")
}


$(document).ready(function(){
	// Activate tooltip
	$("[data-toggle='tooltip']").tooltip({'placement': 'top'});
	

	////////////////////////////// UPDATING loci information /////////////////////////////////////
	// Jquery function for updating distance_cutoff select (dropdown) based on distance_type
	$("input[name='distance_type']").change(function() {
		if ($("input[name='distance_type']:checked").val() == 'ld') {
			$("#input_group_ld_distance_cutoff").show();
			$("#input_group_kb_distance_cutoff").hide();
			var cutoff = $("#ld_distance_cutoff").val() // Copying ld_distance_cutoff to hidden "master" distance_cutoff
			$("#distance_cutoff").val(cutoff)
			// console.log('ld called, val:' + $("input[name='distance_type']:checked").val())
			// console.log( 'distance_type will be set to: ' + cutoff )

		} else if ($("input[name='distance_type']:checked").val() == 'kb') {
			$("#input_group_ld_distance_cutoff").hide();
			$("#input_group_kb_distance_cutoff").show();
			var cutoff = $("#kb_distance_cutoff").val() // Copying kb_distance_cutoff to hidden "master" distance_cutoff
			$("#distance_cutoff").val(cutoff)
			// console.log('kb called, val:' + $("input[name='distance_type']:checked").val())
			// console.log( 'distance_type will be set to: ' + cutoff )
		}
	}) // end change()

	// If ld cutoff selection changes, then update the hidden distance_cutoff variable
	$("#ld_distance_cutoff").change(function() {
		var cutoff = $("#ld_distance_cutoff").val()
		$("#distance_cutoff").val(cutoff)
		// console.log( 'distance_type will be set to: ' + cutoff )
	})
	// If kb cutoff selection changes, then update the hidden distance_cutoff variable
	$("#kb_distance_cutoff").change(function() {
		var cutoff = $("#kb_distance_cutoff").val()
		$("#distance_cutoff").val(cutoff)
		// console.log( 'distance_type will be set to: ' + cutoff )
	})

	var super_population;
	var distance_type;
	var distance_cutoff;
	$( "#button_get_download_info" ).click(function() {
		// var super_population = $("input[name='super_population']").val() // EUR, WAFR, EAS
		var super_population = $("#super_population").val() // EUR, WAFR, EAS
		// alert(super_population)

		if ($("input[name='distance_type']:checked").val() == 'ld') {
			var distance_type = 'ld';
			var distance_cutoff = $("#ld_distance_cutoff").val();
		} else if ($("input[name='distance_type']:checked").val() == 'kb') {
			var distance_type = 'kb';
			var distance_cutoff = $("#kb_distance_cutoff").val();
		}
		
		get_Snpsnap_Database_URL_and_Size(super_population, distance_type, distance_cutoff);
		$("#panel_download_query").show() // by default the panel is hidden (see HTML code)


	});


}) // end .ready


