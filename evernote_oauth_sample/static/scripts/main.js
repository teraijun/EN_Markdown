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
      notes:[],
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
          that.$data.fd.append('guid', $('.notebook').attr('id'));
          var send_files = _.filter(utils.attached_files, function(a){return body.indexOf(a.name)!=-1});
          that.$data.fd.append('files', JSON.stringify(send_files));
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
        },
        import: function(){
          var that = this;
          $.ajax({
            type: "GET",
            url: "/import/",
            dataType: "json",
            success: function(res) {
              that.$data.notes = res.notes;
              // $('#menu1').dropdown('toggle');
            }
          });
        },
        import_content: function(e){
          var that = this;
          var id = $(e.target).attr('id');
          $.ajax({
            type: "POST",
            beforeSend: function(xhr, settings){
              xhr.setRequestHeader("X-CSRFToken", utils.getCookie('csrftoken'));
            },
            url: "/content/",
            dataType: "json",
            data: {note_id: id},
            success: function(res) {
              _.each(res.resources, function(r){
                var obj = {id:r.id, name: r.name, src:r.src, type:r.type, size:r.size};
                utils.attached_files.push(obj);
              });
              if(window.localStorage){
                window.localStorage.setItem('files', JSON.stringify(utils.attached_files));
              }
              that.insert_to_textarea(res);
            }
          });
        },

        insert_to_textarea: function(data){
          var that = this;
          var notes = _.filter(that.$data.notes, function(n){return n.note_id == data.note_id});
          if(notes.length > 0){
            var note = notes[0];
            this.$data.title = note.title;
            var content = data.content.replace(/<div class="ennote">/, '').replace(/<\/div>$/, '');

            // optional options w/defaults
            var options = {
                link_list:  true,    // render links as references, create link list as appendix
                h1_setext:  false,     // underline h1 headers
                h2_setext:  false,     // underline h2 headers
                h_atx_suf:  false,    // header suffixes (###)
                gfm_code:   "```",    // gfm code blocks
                trim_code:  true,     // trim whitespace within <pre><code> blocks (full block, not per line)
                li_bullet:  "*",      // list item bullet style
                hr_char:    "-",      // hr style
                indnt_str:  "    ",   // indentation string
                bold_char:  "*",      // char used for strong
                emph_char:  "_",      // char used for em
                gfm_del:    true,     // ~~strikeout~~ for <del>strikeout</del>
                gfm_tbls:   true,     // markdown-extra tables
                tbl_edges:  true,    // show side edges on tables
                hash_lnks:  true,    // anchors w/hash hrefs as links
                br_only:    false,    // avoid using "  " as line break indicator
                col_pre:    "col ",   // column prefix to use when creating missing headers for tables
                nbsp_spc:   true,    // convert &nbsp; entities in html to regular spaces
                span_tags:  true,     // output spans (ambiguous) using html tags
                div_tags:   true,     // output divs (ambiguous) using html tags
                unsup_tags: {         // handling of unsupported tags, defined in terms of desired output style. if not listed, output = outerHTML
                    // no output
                    ignore: "script style noscript",
                    // eg: "<tag>some content</tag>"
                    inline: "span sup sub i u b center big",
                    // eg: "\n\n<tag>\n\tsome content\n</tag>"
                    block2: "div form fieldset dl header footer address article aside figure hgroup section",
                    // eg: "\n<tag>some content</tag>"
                    block1c: "dt dd caption legend figcaption output",
                    // eg: "\n\n<tag>some content</tag>"
                    block2c: "canvas audio video iframe"
                },
                tag_remap: {          // remap of variants or deprecated tags to internal classes
                    "i": "em",
                    "b": "strong"
                }
            };
            var reMarker = new reMarked(options);
            var markdown = reMarker.render(content);
            this.$data.body = markdown;
            $('#title').val(this.$data.title); 
            $('#input_area').val(markdown);
          }
        }
      }
  });  
}

$(document).ready(function(){
  main();
});