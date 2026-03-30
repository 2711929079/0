











      let src_base =
        window.location.hostname === "github.io"
          ? "https://cdn.jsdelivr.net/gh/king-of-infinite-space/genshin-social-network/page/"
          : ""
      const stylesheet = document.createElement("link")
      stylesheet.type = "text/css"
      stylesheet.href = src_base + "style.css"
      stylesheet.rel = "stylesheet"
      document.head.appendChild(stylesheet)

      const icon = document.createElement("link")
      icon.type = "image/svg+xml"
      icon.href = src_base + "icon.svg"
      icon.rel = "icon"
      document.head.appendChild(icon)
    

      const sc = document.createElement("script")
      sc.src = src_base + "script.js"
      document.body.appendChild(sc)
    