
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function () {
    alert('Copied to clipboard');
  }, function (err) {
    console.error('Could not copy text: ', err);
  });
}
