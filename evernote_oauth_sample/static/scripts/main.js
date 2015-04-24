"use strict";

$(function(){
  new Vue({
    el: '#content',
    data: {
      input: '# hello',
      response:{},
      clipped:{},
      selected: '',
      attached_files:[],
      fd:new FormData()
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
          that.$data.fd.append('title', $('#title').val() || 'Untitled');
          that.$data.fd.append('body', $('#body').html().replace(/ (id|class)[^>]+/g, '').replace('<hr>', '<hr></hr>').replace(/(<img[^>]+>)/,'$1</img>'));
          that.$data.fd.append('guid', $('#notebooks option:selected').val());
          var csrftoken = getCookie('csrftoken');
          var resources = that.resources || '';
          $.ajax({
            type: "POST",
            beforeSend: function(xhr, settings){
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
            },
            data: that.$data.fd,
            url: "/note/",
            dataType: "json",
            processData: false,
            contentType:false,
            success: function(response) {
              console.log(response);
              if (response.status != 'error'){
                that.$data.clipped = response;
                $('#div-modal').modal();
              }
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
          var filesLength = files.length;
          for (var i = 0; i < filesLength; i++) {
            var file = files[i];
            if (file && (file.type && file.type.match(/^image/)
                     || !file.type && file.name.match(/\.(jp[eg]+|png|gif|bmp)$/i))) {
              var reader = new FileReader();
              reader.onload = function (file, i) { return function () {
                var obj = {name: file.name, result: this.result};
                that.$data.attached_files.push(obj);
              }}(file, i);
              reader.readAsDataURL(file);
              that.$data.fd.append('files[]', file);
            }
          }
          console.log('ファイルがアップロードされました。');
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
