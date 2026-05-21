const API_URL = "http://localhost:5000";

async function handleDownload() {
  const input = document.getElementById("urlInput");
  const errorMsg = document.getElementById("errorMsg");
  const loader = document.getElementById("loader");
  const resultCard = document.getElementById("resultCard");
  const btn = document.getElementById("btnDownload");

  const url = input.value.trim();

  errorMsg.textContent = "";
  resultCard.style.display = "none";

  if (!url) {
    errorMsg.textContent = "Colle un lien Instagram d'abord.";
    return;
  }
  if (!url.includes("instagram.com")) {
    errorMsg.textContent = "Ce lien ne ressemble pas à un lien Instagram.";
    return;
  }

  loader.style.display = "flex";
  btn.disabled = true;

  try {
    // Étape 1 — récupère les infos (miniature, titre)
    const infoRes = await fetch(`${API_URL}/api/info`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const info = await infoRes.json();

    if (!infoRes.ok || info.error) {
      errorMsg.textContent = info.error || "Une erreur s'est produite.";
      return;
    }

    // Affiche la carte résultat
    document.getElementById("resultThumb").src = info.thumbnail || "";
    document.getElementById("resultTitle").textContent = info.title || "Vidéo Instagram";

    // Étape 2 — bouton téléchargement via le backend
    const btnSave = document.getElementById("btnSave");
    btnSave.onclick = async function (e) {
      e.preventDefault();
      btnSave.textContent = "⏳ Téléchargement…";
      btnSave.style.opacity = "0.7";

      try {
        const dlRes = await fetch(`${API_URL}/api/download`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url }),
        });

        if (!dlRes.ok) {
          errorMsg.textContent = "Erreur lors du téléchargement.";
          return;
        }

        // Crée un lien temporaire et déclenche le téléchargement
        const blob = await dlRes.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = (info.title || "video_instagram").replace(/[^a-z0-9]/gi, "_") + ".mp4";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(blobUrl);

      } finally {
        btnSave.textContent = "💾 Sauvegarder la vidéo";
        btnSave.style.opacity = "1";
      }
    };

    resultCard.style.display = "flex";

  } catch (err) {
    errorMsg.textContent = "Impossible de contacter le serveur.";
    console.error(err);
  } finally {
    loader.style.display = "none";
    btn.disabled = false;
  }
}

document.getElementById("urlInput").addEventListener("keydown", function (e) {
  if (e.key === "Enter") handleDownload();
});