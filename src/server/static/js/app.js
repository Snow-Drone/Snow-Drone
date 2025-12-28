const imageContainer = document.getElementById('image-gallery');
const lightbox = document.getElementById('lightbox');
const lbImage = document.getElementById('lightbox-image');
const lbCaption = document.getElementById('lightbox-caption');
const lbClose = document.getElementById('lightbox-close');
const lbPrev = document.getElementById('lightbox-prev');
const lbNext = document.getElementById('lightbox-next');

let images = [];
let currentIndex = -1;
let refreshTimer = null;

function buildGallery(items){
    imageContainer.innerHTML = '';
    images = items || [];
    if(images.length === 0){
        const el = document.createElement('div');
        el.className = 'no-images';
        el.textContent = 'No images found yet.';
        imageContainer.appendChild(el);
        return;
    }

    images.forEach((image, idx) => {
        const card = document.createElement('div');
        card.className = 'image-card fade-in';

        const btn = document.createElement('button');
        btn.className = 'image-button';
        btn.setAttribute('aria-label', `Open image ${idx+1}`);
        btn.dataset.index = idx;

        const img = document.createElement('img');
        img.className = 'image-item';
        img.loading = 'lazy';
        img.decoding = 'async';
        img.src = image;
        img.alt = image.split('/').pop() || 'Image';

        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        const cap = document.createElement('div');
        cap.className = 'caption';
        cap.textContent = img.alt;
        overlay.appendChild(cap);

        btn.appendChild(img);
        btn.appendChild(overlay);
        card.appendChild(btn);
        imageContainer.appendChild(card);

        btn.addEventListener('click', () => openLightbox(idx));
    });
}

function fetchImages(){
    fetch('/api/images')
        .then(r => r.json())
        .then(data => {
            // keep order and re-render only when changed
            const incoming = (data.images || []).slice();
            if(JSON.stringify(incoming) !== JSON.stringify(images)){
                buildGallery(incoming);
            }
        })
        .catch(err => console.error('Error fetching images:', err));
}

function openLightbox(idx){
    if(!images[idx]) return;
    currentIndex = idx;
    lbImage.src = images[idx];
    lbImage.alt = images[idx].split('/').pop() || '';
    // show index and file name
    const name = lbImage.alt;
    lbCaption.textContent = `${currentIndex + 1} / ${images.length} — ${name}`;
    lightbox.setAttribute('aria-hidden', 'false');

    // prefetch neighbors
    if(images[idx+1]){ const i=new Image(); i.src = images[idx+1]; }
    if(images[idx-1]){ const i=new Image(); i.src = images[idx-1]; }
}

function closeLightbox(){
    lightbox.setAttribute('aria-hidden', 'true');
    lbImage.src = '';
    currentIndex = -1;
}

function showNext(){ if(images.length===0) return; currentIndex = (currentIndex + 1) % images.length; openLightbox(currentIndex); }
function showPrev(){ if(images.length===0) return; currentIndex = (currentIndex - 1 + images.length) % images.length; openLightbox(currentIndex); }

lbClose.addEventListener('click', closeLightbox);
lbNext.addEventListener('click', showNext);
lbPrev.addEventListener('click', showPrev);

// close when clicking outside image
lightbox.addEventListener('click', (e)=>{ if(e.target === lightbox) closeLightbox(); });

document.addEventListener('keydown', (e)=>{
    if(lightbox.getAttribute('aria-hidden') === 'false'){
        if(e.key === 'Escape') closeLightbox();
        if(e.key === 'ArrowRight') showNext();
        if(e.key === 'ArrowLeft') showPrev();
    }
});

document.addEventListener('visibilitychange', ()=>{ if(document.visibilityState === 'visible') fetchImages(); });

// initial load and periodic refresh
document.addEventListener('DOMContentLoaded', ()=>{
    fetchImages();
    refreshTimer = setInterval(fetchImages, 30000);
});

// export for debugging
window._gallery = { openLightbox, closeLightbox, fetchImages };