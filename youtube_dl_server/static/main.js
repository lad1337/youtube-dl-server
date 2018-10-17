var templates = {}
// from https://stackoverflow.com/a/7616484
String.prototype.hashCode = function() {
  var hash = 0, i, chr;
  if (this.length === 0) return hash;
  for (i = 0; i < this.length; i++) {
    chr   = this.charCodeAt(i);
    hash  = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
};


var template;
var status_class_map = {
    'downloading': '',
    'analysing': '',
    'finished': '',
    'pending': '',
    'error': 'bg-danger',
};
function new_entry(id, item){
    item.class = status_class_map[item.status];
    var inner = template(item);
    return inner;
}

function sort(){
    $("ul.done").each(function(){
        $(this).html($(this).children('li').sort(function(a, b){
            return ($(b).data('at')) < ($(a).data('at')) ? -1 : 1;
        }));
    });
}

function poll_state(){
    $.getJSON('state', function(resp){
        $('#idle').text(resp.workers.idle);
        $('#busy').text(resp.workers.busy);

        var state = resp.state;
        $('li.item').addClass('old');
        for(url in state){
            if (!state.hasOwnProperty(url))
                continue;
            var id = url.hashCode();
            var item = state[url];
            item.id = id;
            item.url = url;
            if(item.status == 'downloading' || item.status == 'finished'){
                var entry = $('ul.downloading .' + id);
                $('ul.pending li.' + id).remove();
                if(entry.length == 0)
                    $('ul.downloading').append(new_entry(id, item));
                else
                    entry.removeClass('old');
                var animate_classes = 'progress-bar-striped progress-bar-animated';
                var bar = $('.progress-bar', entry);
                if (item.status == 'downloading') {
                    bar.removeClass(animate_classes).width(item._percent_str);
                } else { // finished aka transcoding / ffmpeg
                    bar.addClass(animate_classes + ' bg-success')
                    .width('100%');
                }
                $('.speed', entry).text(item._speed_str);
            } else if(item.status == 'done' || item.status == 'error') {
                $('ul.downloading li.' + id).remove();
                $('ul.pending li.' + id).remove();
                var entry = $('ul.done .' + id);
                if(entry.length == 0)
                    $('ul.done').append(new_entry(id, item));
                else
                    entry.removeClass('old');
            } else {
                var entry = $('ul.pending .' + id);
                if(item.status === undefined)
                    item.status = 'pending';
                if(entry.length == 0)
                    $('ul.pending').append(new_entry(id, item));
                else{
                    if(item.status == 'analysing'){
                        $('.progress-bar', entry).width(item._percent_str);
                    }
                    entry.removeClass('old');
                }
            }
        }
        $('li.item.old').remove();
        //sort();
    });

}

$(document).ready(function() {
    window.setInterval(poll_state, 1000);
    var source   = document.getElementById("entry-template").innerHTML;
    template = Handlebars.compile(source);
    $('.navbar form').submit(function(e){
        $('.popover .add-options input').each(function(){
            var t = $(this);
            console.log(t.val());
            $('.navbar form #' + t.attr('id')).val(t.val());
        });
        $.post('q', $(this).serialize(), function(resp){
            console.log(resp);
        });
        e.preventDefault();
        $('[data-toggle="popover"][aria-describedby]').click();
    });
    $('#clear-history').click(function(){
        $.ajax({
            url: 'state/done',
            type: 'DELETE',
        });
    });
    $('[data-toggle="popover"]').popover({
        content: $('.add-options').clone(),
        html: true
    });
});