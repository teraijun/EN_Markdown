"use strict";

new Vue({
  el: '#content',
  data: {
    input: '# hello',
    response:{},
    clipped:{},
    selected: ''
  },
  filters: {
    marked: marked
  },
  created: function() {
    var that = this;
      $.ajax({
        type: "GET",
        url: "/info/",
        dataType: "json",
        success: function(response) {
          that.$data.response = response;
          if (that.$data.response.status == 'redirect') that.$data.response.redirect_url = response.redirect_url+'?callback='+encodeURIComponent(window.location.href);
        }
      });
    },
    methods: {
      clip: function($e){
        var that = this;
        var title = $('#title').val();
        var body = $('#body').html().replace(/ id[^>]+/g, '');
        var guid = $('#notebooks option:selected').val();
        var csrftoken = getCookie('csrftoken');
        $.ajax({
          type: "POST",
          beforeSend: function(xhr, settings){
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
          },
          data: {
            'title': title,
            'body': body,
            'resources': '',
            'guid': guid
          },
          url: "/note/",
          dataType: "json",
          success: function(response) {
            console.log(response);
            that.$data.clipped = response;
            $('#div-modal').modal();
          }
        });
      }
    }
});

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$('#input_area').scroll(function(){
  var height = $(this).scrollTop();
  $("#result div").scrollTop(height);
});
