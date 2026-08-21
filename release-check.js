(() => {
  const expected = String(window.GAMEGRID_RELEASE_VERSION || '').trim();
  const placeholder = '__GAMEGRID_RELEASE_VERSION__';
  let checking = false;
  let prompt = null;

  function showPrompt(version) {
    if (prompt) return;

    const root = document.createElement('div');
    root.className = 'update-prompt';
    root.setAttribute('role', 'status');
    root.setAttribute('aria-live', 'polite');

    const message = document.createElement('span');
    message.textContent = 'New version available — refresh';

    const refresh = document.createElement('button');
    refresh.type = 'button';
    refresh.textContent = 'Refresh';
    refresh.addEventListener('click', () => {
      const url = new URL(window.location.href);
      url.searchParams.set('release', version || String(Date.now()));
      window.location.assign(url.toString());
    });

    const dismiss = document.createElement('button');
    dismiss.type = 'button';
    dismiss.className = 'update-dismiss';
    dismiss.textContent = 'Dismiss';
    dismiss.setAttribute('aria-label', 'Dismiss update notice');
    dismiss.addEventListener('click', () => {
      root.remove();
      prompt = null;
    });

    root.append(message, refresh, dismiss);
    document.body.append(root);
    requestAnimationFrame(() => root.classList.add('show'));
    prompt = root;
  }

  async function check() {
    if (checking || !expected || expected.includes(placeholder)) return false;
    checking = true;
    try {
      const response = await fetch(`./release-version.json?check=${encodeURIComponent(expected)}&t=${Date.now()}`, {
        cache: 'no-store',
        headers: { Accept: 'application/json' },
      });
      if (!response.ok) return false;
      const marker = await response.json();
      const current = String(marker?.version || '').trim();
      if (current && current !== expected) {
        showPrompt(current);
        return true;
      }
    } catch {
      // Release checks are advisory; an unavailable marker must not interrupt play.
    } finally {
      checking = false;
    }
    return false;
  }

  window.GameGridRelease = { check };
  const start = () => { check(); };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) check();
  });
})();
