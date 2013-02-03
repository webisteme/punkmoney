function loadTicker(div, url){

	$.get(url, function(data){

		$(div).html(data);

	});

	timer = setTimeout(function() {loadTicker(url);}, 3000);

}


function search(){

	term = $('input#searchbox').val();
  
	if (term.charAt(0) == '@'){
		term = term.substring(1);
		}
		
	url = '/search/' + escape(term);
	
	$.get(url, function(data){

		window.location = data;

	});
	
}