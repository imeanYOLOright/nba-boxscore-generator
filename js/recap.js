$(function() {
	$(".matchup").each(function(i, el) {
		$el = $(el);
		var home = $el.find(".home").text;
		var away = $el.find(".away").text;
		var date = $(".jumbotron").find("h2").text.split("/");
		var year = date[2];
		var month = date[1];
		var day = date[0].slice(9);
		var postgame = $el.find(".postgame");

		$el.find(".btn").click(function() {
			$.get("/generate", {"home": home,
									  "away": away, 
									  "year": year,
									  "month": month,
									  "day": day
									 }, function(data) {
				postgame.val(data).removeClass("hidden");
			}); 
		}
	});
});
