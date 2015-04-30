"use strict";

var Utils = function(){};

Utils.prototype = {
  attached_files: window.localStorage && window.localStorage.getItem('files') ? JSON.parse(window.localStorage.getItem('files')) : [],
  marked2: function(str){
    if (this.attached_files.length > 0){
        _.each(this.attached_files, function(a){str=str.replace(a.id,a.src)});
      }
      return marked(str);
    },

  store_title: function(str){
    if(window.localStorage){
      window.localStorage.setItem('title', str);
    }
    return str
  },

  store_body: function(str){
    var that = this;
    if(window.localStorage){
      window.localStorage.setItem('body', str);
    }
    return str
  },

  getCookie: function(name) {
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
};

function main(){
  var utils = new Utils;
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

  new Vue({
    el: '#content',
    data: {
      title: window.localStorage && window.localStorage.getItem('title') ? window.localStorage.getItem('title') : '',
      body: window.localStorage && window.localStorage.getItem('body') ? window.localStorage.getItem('body') : '',
      response:{},
      clipped:{},
      selected: '',
      fd:new FormData()
    },
    filters: {
      marked: utils.marked2,
      store_title: utils.store_title,
      store_body: utils.store_body
    },
    ready: function(){
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
    },
    created: function() {
      var that = this;
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
          that.$data.fd.append('title', that.$data.title || 'Untitled');
          var body = utils.marked2(that.$data.body).replace(/ (id|class)[^>]+/g, '').replace(/(<hr>)/g, '$1</hr>').replace(/(<img[^>]+>)/g,'$1</img>');

          _.each(utils.attached_files, function(a){
            var regexp = new RegExp('<img src[^ ]+ alt="'+a.name+'"[^>]+></img>', 'g');
            var replace = '<p id="'+a.name+'"></p>';
            body = body.replace(regexp, replace);
          });

          that.$data.fd.append('body', body);
          that.$data.fd.append('guid', $('#notebooks option:selected').val());
          that.$data.fd.append('files', JSON.stringify(utils.attached_files));
          $.ajax({
            type: "POST",
            beforeSend: function(xhr, settings){
              xhr.setRequestHeader("X-CSRFToken", utils.getCookie('csrftoken'));
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
              reader.onload = function (file) { return function () {
                //edit bynary string
                var src = this.result;
                var input = $('#input_area');
                var input_val = that.$data.body;
                var pos = input.caretPos();
                var id = file.name+'_'+(new Date().getYear());
                var insert = '\n !['+file.name+']('+id+' "'+file.name+'") \n';
                input_val = input_val.substr(0,pos) + insert + input_val.substr(pos, input_val.length);
                input.val(input_val);
                that.$data.body = input_val;
                var obj = {id:id, name: file.name, src:src, type:file.type, size:file.size};
                utils.attached_files.push(obj);
                if(window.localStorage){
                  window.localStorage.setItem('files', JSON.stringify(utils.attached_files));
                }
              }}(file);
              reader.readAsDataURL(file);
              console.log('upload');
            } else {
              console.log('upload only img file');
            }
          }
        },
        showPreview: function(){
          var title = this.$data.title || 'Untitled';
          $('#preview_title').html(utils.marked2(title));
          $('#preview_body').html(utils.marked2(this.$data.body));
          $('#div-modal').modal();
        },
        auth: function(e){
          e.preventDefault();
          var url = $(e.target).attr('href');
          if (url.indexOf('logout')!=-1) window.localStorage.clear();
          window.location.href = url;
        }
      }
  });  
}

$(document).ready(function(){
  main();
});