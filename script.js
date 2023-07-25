
let submitButton = document.querySelector("button");
let artistInput = document.querySelector("#artistInput");
let artistValue = artistInput.value;

let url  = `https://en.wikipedia.org/wiki/${artistValue}`;


submitButton.addEventListener("click", () => {
    window.open(url, '_blank');
});