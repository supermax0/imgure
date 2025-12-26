function upload() {
  const files = document.getElementById("files").files;
  const visibility = document.getElementById("visibility").value;
  const bar = document.getElementById("bar");

  const form = new FormData();
  for (let f of files) form.append("images", f);
  form.append("visibility", visibility);

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "http://127.0.0.1:5000/upload");

  xhr.setRequestHeader("Authorization", "Bearer SUPER_SECRET_TOKEN");

  xhr.upload.onprogress = e => {
    const percent = Math.round((e.loaded / e.total) * 100);
    bar.style.width = percent + "%";
  };

  xhr.onload = () => {
    const data = JSON.parse(xhr.responseText);

    const g = document.getElementById("gallery");
    g.innerHTML = "";

    data.images.forEach(u => {
      const img = document.createElement("img");
      img.src = "http://127.0.0.1:5000" + u;
      g.appendChild(img);
    });

    document.getElementById("links").innerHTML = `
      🔗 رابط الألبوم:
      <a href="http://127.0.0.1:5000${data.album_url}" target="_blank">${data.album_url}</a><br>
      📦 تحميل ZIP:
      <a href="http://127.0.0.1:5000${data.zip_url}" target="_blank">${data.zip_url}</a>
    `;
  };

  xhr.send(form);
}
