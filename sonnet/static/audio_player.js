//
// var player = document.createElement("AUDIO");
// player.src = '/static/tracks/45384434f60fd02c.mp3';
//
// $('#play').click(function(){
//   player.play();
// });
//
// function conta(){
//     $('#counter').html(msToHMS(parseInt(player.currentTime*1000)));
//     $('#info').html('');
//     setTimeout(conta,250);
// }
// setTimeout(conta,0);
//
// player.addEventListener('timeupdate',function(){
//
// },false);
//
//
//
// function msToHMS( ms ) {
//     // 1- Convert to seconds:
//     var seconds = ms / 1000;
//     // 2- Extract hours:
//     var hours = String('00' + parseInt( seconds / 3600 )).slice(-2); // 3,600 seconds in 1 hour
//     seconds = seconds % 3600; // seconds remaining after extracting hours
//     // 3- Extract minutes:
//     var minutes = String('00' + parseInt( seconds / 60 )).slice(-2); // 60 seconds in 1 minute
//     // 4- Keep only seconds not extracted to minutes:
//     seconds = seconds % 60;
//
//     var mili = String(ms).substr(String(ms).length - 3);
//     var seconds2 = String('00' + parseInt( seconds)).slice(-2);
//
//     return(hours+":"+minutes+":"+ seconds2 +'.'+ mili);
// }



var music = document.getElementById('music'); // id for audio element
     var duration = music.duration; // Duration of audio clip, calculated here for embedding purposes
     var pButton = document.getElementById('pButton'); // play button
     var playhead = document.getElementById('playhead'); // playhead
     var timeline = document.getElementById('timeline'); // timeline

     // timeline width adjusted for playhead
     var timelineWidth = timeline.offsetWidth - playhead.offsetWidth;

     // play button event listenter
     pButton.addEventListener("click", play);

     // timeupdate event listener
     music.addEventListener("timeupdate", timeUpdate, false);

     // makes timeline clickable
     timeline.addEventListener("click", function (event) {
         moveplayhead(event);
         music.currentTime = duration * clickPercent(event);
     }, false);

     // returns click as decimal (.77) of the total timelineWidth
     function clickPercent(event) {
         return (event.clientX - getPosition(timeline)) / timelineWidth;
     }

     // makes playhead draggable
     playhead.addEventListener('mousedown', mouseDown, false);
     window.addEventListener('mouseup', mouseUp, false);

     // Boolean value so that audio position is updated only when the playhead is released
     var onplayhead = false;

     // mouseDown EventListener
     function mouseDown() {
         onplayhead = true;
         window.addEventListener('mousemove', moveplayhead, true);
         music.removeEventListener('timeupdate', timeUpdate, false);
     }

     // mouseUp EventListener
     // getting input from all mouse clicks
     function mouseUp(event) {
         if (onplayhead == true) {
             moveplayhead(event);
             window.removeEventListener('mousemove', moveplayhead, true);
             // change current time
             music.currentTime = duration * clickPercent(event);
             music.addEventListener('timeupdate', timeUpdate, false);
         }
         onplayhead = false;
     }
     // mousemove EventListener
     // Moves playhead as user drags
     function moveplayhead(event) {
         var newMargLeft = event.clientX - getPosition(timeline);

         if (newMargLeft >= 0 && newMargLeft <= timelineWidth) {
             playhead.style.marginLeft = newMargLeft + "px";
         }
         if (newMargLeft < 0) {
             playhead.style.marginLeft = "0px";
         }
         if (newMargLeft > timelineWidth) {
             playhead.style.marginLeft = timelineWidth + "px";
         }
     }

     // timeUpdate
     // Synchronizes playhead position with current point in audio
     function timeUpdate() {
         var playPercent = timelineWidth * (music.currentTime / duration);
         playhead.style.marginLeft = playPercent + "px";
         if (music.currentTime == duration) {
             pButton.className = "";
             pButton.className = "fas fa-play";
         }
     }

     //Play and Pause
     function play() {
         // start music
         if (music.paused) {
             music.play();
             // remove play, add pause
             pButton.className = "";
             pButton.className = "fas fa-pause";
         } else { // pause music
             music.pause();
             // remove pause, add play
             pButton.className = "";
             pButton.className = "fas fa-play";
         }
     }

     // Gets audio file duration
     music.addEventListener("canplaythrough", function () {
         duration = music.duration;
     }, false);

     // getPosition
     // Returns elements left position relative to top-left of viewport
     function getPosition(el) {
         return el.getBoundingClientRect().left;
     }
