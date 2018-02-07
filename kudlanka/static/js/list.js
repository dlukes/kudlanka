$(document).ready(function () {

  // add filter inputs to seg-table footer
  $("#seg-table tfoot th").each(function () {
    var title = $("#seg-table thead th").eq($(this).index()).text();
    $(this).html('<input type="text" placeholder="' + title + '" />');
  });

  var l10n;
  if (LOCALE === 'cs') {
    l10n = 'Czech.lang';
  } else {
    l10n = 'English.lang';
  }
  l10nUrl = ROOT + '/static/vendor/datatables-plugins/i18n/' + l10n;
  var dtInit = {
    order: [],
    language: {
      url: l10nUrl
    }
  };

  // initialize data table
  var dt = $("#seg-table").DataTable(dtInit);
  dtInit.pageLength = 5;
  dtInit.lengthMenu = [5, 10, 25, 50, 100];
  $("#batch-table").DataTable(dtInit);

  // wire up seg-table column filtering
  dt.columns().every(function () {
    var that = this;
    $("input", this.footer()).on("keyup change", function () {
      that.search(this.value).draw();
    });
  });

});
