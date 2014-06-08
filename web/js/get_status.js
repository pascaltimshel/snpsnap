$(document).ready(function(){
	var sid = $('#session_id').val();
	//alert("function called: "+ sid)
	var progresspump = setInterval(function(){
	$.ajax({
		url:"/app/status.py",
		data: "session_id="+sid,
		dataType: "json",
		success: function(response){
			//var data = $.parseJSON(response.d);
			//alert("succes")
			//alert(response)
			$("#match_progress").val(response);
			$("#match_percentage").html(response + "%");

			if (data.value == 100) {
			isDone = true;
			clearInterval(myInterval);
		}
	})
	}, 1000)
 })
