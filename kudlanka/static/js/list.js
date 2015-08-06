$(document).ready(function () {

  // add filter inputs to footer
  $("#seg-table tfoot th").each(function () {
    var title = $("#seg-table thead th").eq($(this).index()).text();
    $(this).html('<input type="text" placeholder="' + title + '" />');
  });

  // initialize data table
  var dt = $("#seg-table").DataTable({
    order: [],
    language: {
      "sProcessing":   "Provádím...",
      "sLengthMenu":   "Zobraz záznamů _MENU_",
      "sZeroRecords":  "Žádné záznamy nebyly nalezeny",
      "sInfo":         "Zobrazuji _START_ až _END_ z celkem _TOTAL_ záznamů",
      "sInfoEmpty":    "Žádné záznamy k zobrazení",
      "sInfoFiltered": "(filtrováno z celkem _MAX_ záznamů)",
      "sInfoPostFix":  "",
      "sSearch":       "Hledat:",
      "sUrl":          "",
      "oPaginate": {
        "sFirst":    "První",
        "sPrevious": "Předchozí",
        "sNext":     "Další",
        "sLast":     "Poslední"
      }
    }
  });

  // apply filter criteria
  dt.columns().every(function () {
    var that = this;
    $("input", this.footer()).on("keyup change", function () {
      that.search(this.value).draw();
    });
  });

});
