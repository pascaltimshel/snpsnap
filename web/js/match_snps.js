$(document).ready(function(){
	// Activate tooltip
	$("[data-toggle='tooltip']").tooltip({'placement': 'top'});
	
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
		errorClass: "error", // this is default
		// errorClass: 'help-block', // Consider using this
		validClass: "valid", // this is default
		errorElement: 'label', // this is default. This makes sense to relate the error to the input
		rules: {
			max_freq_deviation: {
				required: true,
				digits: true,
				min: 0,
				max: 50
			},
			max_genes_count_deviation: {
				required: true,
				digits: true,
				min: 1
			},
			max_distance_deviation: {
				required: true,
				digits: true,
				min: 1
			},
			N_sample_sets: {
				required: true,
				digits: true,
				min: 1,
				max: 10000
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
		groups: {
		   dummyName: "snplist_text snplist_fileupload"
		},
		messages: {
			job_name: {
				required: "Please specify a job name to allow identification of this job"
			},
			snplist_text: { 
				require_from_group: "Please either paste in your SNPs or upload a SNPlist file"
			},
			snplist_fileupload: { 
				require_from_group: "Please either paste in your SNPs or upload a SNPlist file"
			}
		},
		// highlight - How to highlight invalid fields. default: Adds errorClass to the element
		// element (Type: Element): The invalid DOM element, usually an input.
		highlight: function(element) {
			$(element).closest('.form-group').removeClass('has-success').addClass('has-error');
			$(element).closest('.form-group').find('.form-control-feedback').removeClass('glyphicon-ok').addClass('glyphicon-remove');
			// console.log("highlight function was called")
		},

		// unhighlight - SEE highlight for more info
		unhighlight: function (element) {
			$(element).closest('.form-group').removeClass('has-error').addClass('has-success');
			$(element).closest('.form-group').find('.form-control-feedback').removeClass('glyphicon-remove').addClass('glyphicon-ok');
		},

		// $(element).closest('fieldset').find('.form-group').first().removeClass('has-success').addClass('has-error');
		
		/// THIS FUNCTION WORKS JUST FINE - KEEP IT!
		/// success - If specified, the error label is displayed to show a valid element
		// success: function(label) { //function(label, element)
		// 	console.log('success'); // That logs success any time a valid input is made. 
		// 	label
		// 	.text('OK!').addClass('valid')
		// 	.closest('.form-group').removeClass('has-error').addClass('has-success');
		// 	// console.log("success function was called")
		// },

		// error (Type: jQuery): the error label to insert into the DOM.
		// element (Type: jQuery): the validated input, for relative positioning
		errorPlacement: function(error, element) {
			// error.insertAfter(element); // this is default
			// error.appendTo( element.parent("td").next("td") ); // just an example

			// Using input groups
			if (element.attr("name") == "snplist_text" || element.attr("name") == "snplist_fileupload" ) {
				element.closest('fieldset').find('.error_msg_place').first().append(error)
			} else {
				// element.parent().next('.error_msg_place').append(error)
				element.closest('.form-group').children('.error_msg_place').append(error)
				// parent is the immideate parrent
				// parents traverses all the way up the DOM tree
			}

			// See also http://api.jquery.com/category/traversing/
			// error.appendTo(element.next(".error_msg_place"))
			// element.parent().next('.error_msg_place').html('sadasdas') // use this for inserting text in field

			// ABOUT after vs append
			// http://stackoverflow.com/questions/14846506/append-prepend-after-and-before
			// .after() puts the element after the element
			// .append() puts data inside an element at last index and
		}

		// if (element.parent('.input-group').length) {
		// 	error.insertAfter(element.parent());
		// errorPlacement: function(error, element) {
		// }

	}); // end .validate
}) // end .ready




// // SEE MORE AT http://stackoverflow.com/questions/3671300/jquery-validation-groups
// groups: {
//    username: "fname lname"
//  },
//  errorPlacement: function(error, element) {
//    if (element.attr("name") == "fname" || element.attr("name") == "lname" ) {
//      error.insertAfter("#lastname");
//    } else {
//      error.insertAfter(element);
//    }
//  }
