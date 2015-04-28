"use strict";

$(function(){
  var attached_files = [];
  marked.setOptions({
    renderer: new marked.Renderer(),
    gfm: true,
    tables: true,
    breaks: false,
    pedantic: false,
    sanitize: true,
    smartLists: true,
    smartypants: false
  });

  function marked2(str){
    if (attached_files.length > 0){
      _.each(attached_files, function(a){str=str.replace(a.id,a.result)});
    }
    return marked(str);
  }


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


  new Vue({
    el: '#content',
    data: {
      input: '',
      response:{},
      clipped:{},
      selected: '',
      fd:new FormData()
    },
    filters: {
      marked: marked2
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
        $('#input_area').bind('drop', function(e){
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
          var input_val = $('#input_area').val();
          $('#body').html(marked2(input_val));
          var body = $('#body').html().replace(/ (id|class)[^>]+/g, '').replace(/(<hr>)/g, '$1</hr>').replace(/(<img[^>]+>)/g,'$1</img>');

          _.each(attached_files, function(a){
            var regexp = new RegExp('<img src[^ ]+ alt="'+a.name+'"[^>]+></img>', 'g');
            var replace = '<p id="'+a.name+'"></p>';
            body = body.replace(regexp, replace);
          });

          that.$data.fd.append('body', body);
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
                $('#clip').attr('data-content', response.note.title);
                $('#clip').popover('toggle');
                setTimeout(function(){
                  $('#clip').popover('hide');
                },3000)
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
                var input = $('#input_area');
                var input_val = input.val();
                var pos = input.caretPos();
                var id = file.name+'_'+(new Date().getYear());
                var insert = '\n\n !['+file.name+']('+id+' "'+file.name+'") \n\n';
                input_val = input_val.substr(0,pos) + insert + input_val.substr(pos, input_val.length);
                input.val(input_val);
                var obj = {id:id, name: file.name, result: this.result};
                attached_files.push(obj);
              }}(file, i);
              reader.readAsDataURL(file);
              that.$data.fd.append('files[]', file);
              console.log('upload');
            } else {
              console.log('upload only img file');
            }
          }
        },
        showPreview: function(){
          var input_val = $('#input_area').val();
          $('#body').html(marked2(input_val));
          $('#div-modal').modal();
        }
      }
  });
});