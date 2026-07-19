export function fadeTo(location: string, durationMs = 700): Promise<void> {
  return new Promise(() => {
    const old = document.createElement('div')
    old.style.cssText = `
      position:fixed;inset:0;z-index:2147483647;
      background:rgba(255,255,255,1);opacity:0;
      pointer-events:none;
      transition:opacity ${durationMs}ms ease;
    `
    document.body.appendChild(old)
    requestAnimationFrame(() => {
      old.style.opacity = '1'
      setTimeout(() => {
        window.location.href = location
      }, durationMs * 0.7)
    })
  })
}

export function blurFade(durationMs = 700): Promise<void> {
  return new Promise((resolve) => {
    const app = document.getElementById('app')
    if (!app) { resolve(); return }
    app.style.transition = `opacity ${durationMs}ms ease, filter ${durationMs}ms ease`
    app.style.opacity = '0'
    app.style.filter = 'blur(16px) brightness(1.4)'
    setTimeout(resolve, durationMs)
  })
}
