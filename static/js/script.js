function pasteURL() {
    navigator.clipboard.readText().then(text => {
        document.getElementById('url').value = text;
    });
}

document.getElementById('download-form').addEventListener('submit', function(event) {
    event.preventDefault();
    document.getElementById('status').textContent = 'İndirme işlemi başlatıldı. Lütfen bekleyin...';

    fetch(event.target.action, {
        method: 'POST',
        body: new FormData(event.target)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        const url = data.url;
        const filename = data.filename;
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        document.getElementById('status').textContent = 'İndirme işlemi tamamlandı.';
    })
    .catch(error => {
        console.error('Hata:', error);
        document.getElementById('status').textContent = 'İndirme işlemi sırasında bir hata oluştu: ' + error.message;
    });
});

document.getElementById('url').addEventListener('input', function() {
    if (this.value.length > 10) {
        fetch('/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({url: this.value})
        })
        .then(response => response.json())
        .then(data => {
            const preview = document.getElementById('preview');
            preview.innerHTML =
                <img src="${data.thumbnail}" alt="Video thumbnail" style="max-width: 100%;">
                <p><strong>${data.title}</strong></p>
                <p>Süre: ${Math.floor(data.duration / 60)}:${(data.duration % 60).toString().padStart(2, '0')}</p>
            ;
        })
        .catch(error => {
            console.error('Önizleme hatası:', error);
            document.getElementById('preview').textContent = 'Video bilgileri yüklenemedi.';
        });
    } else {
        document.getElementById('preview').innerHTML = '';
    }
});