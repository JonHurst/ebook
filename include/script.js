$(function() {
    $("div[class='bsp_block']").each(
      function() {
        var bspid = $(this).text().split("…")[0];
        var text = $(this).text();
        $(this).text("");
        $(this).append("<a href='bsps.xhtml#" + bspid + "'>" + text + "</a>");
      });
});  
