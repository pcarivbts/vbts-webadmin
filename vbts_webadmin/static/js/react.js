$( document ).ready(function() {
	$('.datepicker').datepicker({
      changeMonth: true,
      changeYear: true,
      yearRange: "1900:2012",
    });
    $('[data-toggle="tooltip"]').tooltip();
});

