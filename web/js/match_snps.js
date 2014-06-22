$(document).ready(function(){
	// Activate tooltip
	$("[data-toggle='tooltip']").tooltip({'placement': 'top'});
	
	// Jquery function for updating distance_cutoff select (dropdown) based on distance_type
	$("input[name='distance_type']").change(function() {
		if ($("input[name='distance_type']:checked").val() == 'ld') {
			$("#ld_distance_cutoff").show();
			$("#kb_distance_cutoff").hide();
			console.log('ld called, val:' + $("input[name='distance_type']:checked").val())
		} else if ($("input[name='distance_type']:checked").val() == 'kb') {
			$("#ld_distance_cutoff").hide();
			$("#kb_distance_cutoff").show();
			console.log('kb called, val:' + $("input[name='distance_type']:checked").val())
		}

	});

	$('#snp_example_link').click(function() { //this will apply to the snp example anchor tag
		var example_snp_input_str = 
			["14:69873335",
			"9:5453460",
			"7:88660988",
			"1:201688955",
			"1:181844943",
			"18:67015865",
			"6:32592119",
			"4:58923290",
			"4:59511935",
			"2:73321971"].join('\n');
		$('#snplist_text').val(example_snp_input_str); //this puts the example_snp_input_str inside the textarea for the id labeled 'snplist_text'
	});

// http://stackoverflow.com/questions/20316117/error-placement-with-selectpicker-jquery-validation-plugins
// errorPlacement: function (error, element) {
//     if ($(element).is('select')) {
//         element.next().after(error); // special placement for select elements
//     } else {
//         error.insertAfter(element);  // default placement for everything else
//     }
// }
	$('#snpsnap_match_form').validate( { // initialize the plugin
		rules: {
			max_freq_deviation: {
				required: true,
				digits: true
			},
			max_genes_count_deviation: {
				required: true,
				digits: true
			},
			max_distance_deviation: {
				required: true,
				digits: true
			},
			N_sample_sets: {
				required: true,
				digits: true,
				min: 1,
				max: 5000
			},
			email_address: {
				required: true,
				email: true
			},
			job_name: {
				required: true,
				minlength: 3,
				maxlength: 30
			},
			snplist_text: {
				require_from_group: [1, ".snp_input_group"]
			},
			snplist_fileupload: {
				require_from_group: [1, ".snp_input_group"]
			}
		}, 
		highlight: function(element) { 
			$(element).closest('.form-group').removeClass('has-success').addClass('has-error');
			// console.log("highlight function was called")
		},
		success: function(element) {
		  element
		  .text('OK!').addClass('valid')
		  .closest('.form-group').removeClass('has-error').addClass('has-success');
		  // console.log("success function was called")
		}
		// success: function(element) {
		//   $(element).text('OK!').addClass('valid')
		//   // $(element).closest('.form-group').removeClass('has-error').addClass('has-success');
		// }
	}); // end .validate
}) // end .ready
