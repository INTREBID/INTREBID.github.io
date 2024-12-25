
function copyToClipboard(textToCopy) {
  // 尝试使用navigator.clipboard.writeText，这是现代浏览器推荐的方法
  if (navigator.clipboard && navigator.clipboard.writeText) {
    copyTextWithClipboardAPI(textToCopy);
  } else {
    // 如果不支持，则使用textarea和execCommand的回退方案
    copyTextWithTextAreaFallback(textToCopy);
  }
}

async function copyTextWithClipboardAPI(textToCopy) {
  try {
      await navigator.clipboard.writeText(textToCopy);
      alert('内容已复制！');
  } catch (err) {
      handleCopyError(err);
  }
}

function copyTextWithTextAreaFallback(textToCopy) {
  const textarea = document.createElement('textarea');
  textarea.value = textToCopy;
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px'; // 隐藏textarea
  document.body.appendChild(textarea);
  textarea.select();
  try {
      document.execCommand('copy');
      alert('内容已复制！');
  } catch (err) {
      handleCopyError(err);
  } finally {
      document.body.removeChild(textarea);
  }
}

function handleCopyError(error) {
  console.error('复制失败:', error);
  alert('复制失败，请检查浏览器是否支持该功能或是否有相应权限。');
}
