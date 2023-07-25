artist = "Paramore" // "Tyler the Creator"
popularity = 90

function init() {
    url = `http://127.0.0.1:5501/api/v1.0/${artist}/${popularity}`
    d3.json(url).then(function(data){
        console.log(data)
    })
console.log(url)
}



$(document).ready(function() {
    var musicList = "<ul><li>Song1</li><li>Song another</li></ul>";

    $("#music").append(musicList);
    init();
});
