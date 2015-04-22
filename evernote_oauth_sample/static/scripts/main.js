"use strict";

$(function(){
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
            that.$data.response.redirect_url = response.redirect_url+'?callback='+encodeURIComponent(window.location.href);
          }
        });
        $('.input_area_all').bind('drop', function(e){
            // デフォルトの挙動を停止
            e.preventDefault();
         
            // ファイル情報を取得
            var files = e.originalEvent.dataTransfer.files;
            that.uploadFiles(files);
          }).bind('dragenter', function(){
            // デフォルトの挙動を停止
            return false;
          }).bind('dragover', function(){
            // デフォルトの挙動を停止
            return false;
          });
      },
      methods: {
        clip: function($e){
          var that = this;
          var title = $('#title').val();
          var body = $('#body').html().replace(/ (id|class)[^>]+/g, '').replace('<hr>', '<hr></hr>');
          var guid = $('#notebooks option:selected').val();
          var csrftoken = getCookie('csrftoken');
          var resources = that.resources || '';
          $.ajax({
            type: "POST",
            beforeSend: function(xhr, settings){
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            data: {
              'title': title,
              'body': body,
              'resources': resources,
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
        },
        scroll:function(e){
          var height = $(e.target).scrollTop();
          $("#result div").scrollTop(height);        
        },
        uploadTrigger:function(){
          $('input[type="file"]').click();          
        },
        uploadInput:function(e){
          var files = e.target.files;
          this.uploadFiles(files);
        },
        uploadFiles:function(files){
          var that = this;
          var fd = new FormData();
          var filesLength = files.length;
          var width = $('#body').width() - 10;
          for (var i = 0; i < filesLength; i++) {
            var file = files[i];
            fd.append("files[]", file);
            if (file && (file.type && file.type.match(/^image/)
                     || !file.type && file.name.match(/\.(jp[eg]+|png|gif|bmp)$/i))) {
              var reader = new FileReader();
              reader.onload = function (file, i) { return function () {
                var input = $('#input_area').val();
                var add = input + '!['+file.name+']('+this.result+' "'+file.name+'")';
                $('#input_area').val(add);
              }}(file, i);
              reader.readAsDataURL(file);
            }
          }
          that.resources = fd;
          console.log('ファイルがアップロードされました。');
          // $.ajax({
          //   url: 'アップロード処理をするファイルのパス',
          //   type: 'POST',
          //   data: fd,
          //   processData: false,
          //   contentType: false,
          //   success: function(data) {
          //   }
          // });
        }
      }
  });

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
