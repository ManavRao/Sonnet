
var player = document.createElement("AUDIO");
player.src = '/static/tracks/28c37e4af279fb2d.mp3';

$('#play').click(function(){
  player.play();
});

function conta(){
    $('#counter').html(msToHMS(parseInt(player.currentTime*1000)));
    $('#info').html('');
    setTimeout(conta,250);
}
setTimeout(conta,0);

player.addEventListener('timeupdate',function(){

},false);



function msToHMS( ms ) {
    // 1- Convert to seconds:
    var seconds = ms / 1000;
    // 2- Extract hours:
    var hours = String('00' + parseInt( seconds / 3600 )).slice(-2); // 3,600 seconds in 1 hour
    seconds = seconds % 3600; // seconds remaining after extracting hours
    // 3- Extract minutes:
    var minutes = String('00' + parseInt( seconds / 60 )).slice(-2); // 60 seconds in 1 minute
    // 4- Keep only seconds not extracted to minutes:
    seconds = seconds % 60;

    var mili = String(ms).substr(String(ms).length - 3);
    var seconds2 = String('00' + parseInt( seconds)).slice(-2);

    return(hours+":"+minutes+":"+ seconds2 +'.'+ mili);
}
