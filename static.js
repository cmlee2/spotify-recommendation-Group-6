artist = "Tyler the Creator"
popularity = 60

url = `http://127.0.0.1:5501/api/v1.0/${artist}/${popularity}`
d3.json(url).then(function(data){
    console.log(data)
})
console.log(url)
