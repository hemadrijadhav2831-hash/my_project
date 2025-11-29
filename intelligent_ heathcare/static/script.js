const btn = document.getElementById("start");
const text = document.getElementById("vtext");

if (btn) {
    btn.onclick = () => {
        let rec = new webkitSpeechRecognition();
        rec.lang = "en-IN";
        rec.onresult = (e) => {
            text.value = e.results[0][0].transcript;
        };
        rec.start();
    };
}
