function flashCopied(btn) {
  var original = btn.textContent;
  btn.textContent = 'Copied!';
  btn.classList.add('copied');
  setTimeout(function () {
    btn.textContent = original;
    btn.classList.remove('copied');
  }, 1500);
}
function fallbackCopy(text) {
  var ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand('copy'); } catch (e) {}
  document.body.removeChild(ta);
}
document.querySelectorAll('.copy-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var el = document.getElementById(btn.getAttribute('data-copy-target'));
    if (!el) return;
    var text = el.textContent;
    var done = false;
    var finish = function () {
      if (done) return;
      done = true;
      flashCopied(btn);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      // Some environments never resolve/reject this promise (e.g. blocked
      // permission prompts), so race it against a fallback timeout.
      setTimeout(function () {
        if (!done) { fallbackCopy(text); finish(); }
      }, 400);
      navigator.clipboard.writeText(text).then(finish, function () {
        fallbackCopy(text);
        finish();
      });
    } else {
      fallbackCopy(text);
      finish();
    }
  });
});
