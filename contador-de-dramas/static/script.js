
const EMOJIS = ['😌','🙂','😊','😯','😕','😬','😟','😫','😤','😭','💥'];
function updateEmoji(rangeId, emojiId, valueId){
  const r = document.getElementById(rangeId);
  const e = document.getElementById(emojiId);
  const v = document.getElementById(valueId);
  if(!r||!e||!v) return;
  const i = Math.max(0, Math.min(10, parseInt(r.value||0)));
  e.textContent = EMOJIS[i];
  v.textContent = i;
}
