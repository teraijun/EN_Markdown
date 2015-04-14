new Vue({
  el: '#content',
  data: {
    input: '# hello',
    response:{},
    result: {list: []}
  },
  filters: {
    marked: marked
  },
  created: function() {
    var that = this;
      $.ajax({
        type: "GET",
        url: "/callback/",
        dataType: "json",
        success: function(response) {
          that.$data.response = response;
          if (that.$data.response.status == 'redirect') that.$data.response.redirect_url = response.redirect_url+'?callback='+encodeURIComponent(window.location.href);
        }
      });
    },
    methods: {
      showDetail: function(id, $e){
      // アイテムがクリックされた時のハンドラ
      }
    }
});

$('#input_area').scroll(function(){
  var height = $(this).scrollTop();
  $("#result div").scrollTop(height);
});
