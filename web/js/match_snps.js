// Function to detect file upload
// Taken from: http://stackoverflow.com/a/18164555 
$(document).on('change', '.btn-file :file', function() {
  var input = $(this),
	  numFiles = input.get(0).files ? input.get(0).files.length : 1,
	  label = input.val().replace(/\\/g, '/').replace(/.*\//, '');
  input.trigger('fileselect', [numFiles, label]);
});



$(document).ready(function(){
	// Activate tooltip
	$("[data-toggle='tooltip']").tooltip({'placement': 'top'});
	

	// USER FEEDBACK FOR FILE UPLOAD
	// Taken from: http://stackoverflow.com/a/18164555 
	$('.btn-file :file').on('fileselect', function(event, numFiles, label) {
		// the input variable will be a HTML text element under the input-group class, e.g. <input type="text" class="form-control" readonly>
		var input = $(this).parents('.input-group').find(':text'),
			log = numFiles > 1 ? numFiles + ' files selected' : label;
			// if more than one file is uploaded: log variable will contain the string: e.g. "3 files selected"
			// if ONE file is uploaded: log variable will contain 'cleaned' filename, e.g. 'sample_10randSNPs.list'
		
		if( input.length ) {
			input.val(log); // Set value of text element. Make sure that the HTML text tag has the 'readonly' attribute so the user cannot edit the text. E.g. <input type="text" class="form-control" readonly>
		} else {
			if( log ) alert(log); // Use a warning to inform the user what file has been uploaded
		}
		
	});

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

	////////////////////////////// UPDATING clumping information /////////////////////////////////////
	$("#clump").change(function() {
		if (this.checked) {
			$("#clump_parameter_div").show();
		 } else {
			$("#clump_parameter_div").hide();
		 }
		
	});

	////////////////////////////// EXAMPLE SNP input /////////////////////////////////////
	$('#snp_example_link_chrpos').click(function() { //this will apply to the snp example anchor tag
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

	$('#snp_example_link_rsID').click(function() { //this will apply to the snp example anchor tag
		var example_snp_input_str = 
			["rs10131464",
			"rs79855302",
			"rs12111706",
			"rs67146338",
			"rs59824113",
			"rs111462038",
			"rs143056833",
			"rs35886686",
			"rs727470"].join('\n');
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

	//SEE BELOW LINK for more info about this.optional(element) in jQuery validation method: 
		// ---> http://stackoverflow.com/questions/13093971/what-does-this-optionalelement-do-when-adding-a-jquery-validation-method
	// GOT REGEX METHOD FROM: http://stackoverflow.com/questions/280759/jquery-validate-how-to-add-a-rule-for-regular-expression-validation
	$.validator.addMethod("regex", function(value, element, regexp) {
		var re = new RegExp(regexp);
		return this.optional(element) || re.test(value);
	}, "Your input does not match a valid pattern" );

	// FORM VALIDATION
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
			max_ld_buddy_count_deviation: {
				required: true,
				digits: true,
				min: 1
			},
			N_sample_sets: {
				required: true,
				digits: true,
				min: 1,
				max: 20000
			},
			email_address: {
				required: true,
				email: true
			},
			job_name: {
				required: true,
				minlength: 3,
				maxlength: 100,
				// regex: "^[a-zA-Z0-9_\-]{3,30}$"  // the {3,30} is a bit redundant given the min and max length
				regex: "^[a-zA-Z0-9_\-]+$" // consider using this pattern: [\w._\-]+
			},
			snplist_text: {
				require_from_group: [1, ".snp_input_group"]
			},
			snplist_fileupload: {
				require_from_group: [1, ".snp_input_group"]
			},
			clump_r2: {
				required: true
			},
			clump_kb: {
				required: true,
				digits: true,
				min: 1
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
			},
			job_name: {
				regex: 'only letters (a-z), numbers, underscores and hyphens are allowed' //input pattern must match [a-zA-Z0-9_-]:
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
