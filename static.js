artist = "jpegmafia"
popularity = 60

url2 = `http://127.0.0.1:5501/api/v1.0/${artist}/${popularity}`
d3.json(url2, {
    headers: new Headers({
      "Access-Control-Allow-Origin": true
    }),
}).then(function(data){
    console.log(data)
})

url2 = `http://127.0.0.1:5501/api/v1.0/${artist}`
d3.json(url2, {
    headers: new Headers({
      "Access-Control-Allow-Origin": true
    }),
}).then(function(data){
    console.log(data)
})


// .header('Access-Control-Allow-Origin',true)