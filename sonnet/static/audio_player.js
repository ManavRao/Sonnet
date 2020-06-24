var music = document.getElementById('music'); // id for audio element
var duration = music.duration; // Duration of audio clip, calculated here for embedding purposes
var pButton = document.getElementById('pButton'); // play button
var playhead = document.getElementById('playhead'); // playhead
var timeline = document.getElementById('timeline'); // timeline

// length of song i.e. timeline
var timelineWidth = timeline.offsetWidth - playhead.offsetWidth;

// to check play button event
pButton.addEventListener("click", play);

// updating time as music proceeds
music.addEventListener("timeupdate", timeUpdate, false);

// makes timeline clickable
timeline.addEventListener("click", function (event) {
   moveplayhead(event);
   music.currentTime = duration * clickPercent(event);
}, false);

// function to convert mouse click to x-position
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

// getPosition to calculate remaining song length
// Returns elements left position relative to top-left of viewport
function getPosition(el) {
   return el.getBoundingClientRect().left;
}

//stop and hide the player
function stop_muic() {
    music.pause();
    document.getElementById('controles').style.display = 'none';
}

//main function
function set_music(id1, id2) {
  document.getElementById('controles').style.display = 'block';
  document.getElementById('music').src = id1; //updating song source
  document.getElementById('song_title_player').innerHTML = id2; //updating the song title
  var temp = document.getElementById('music');
  music = temp;
  duration = temp.duration; // Duration of audio clip, recalculated according to song selected
  timelineWidth = timeline.offsetWidth - playhead.offsetWidth; //re-setting the width of seek
  play(); //playing the song
}
