const images = ["/static/image/banner.png", "/static/image/banner_1.png"];

let currentIndex = 0;

function changeImage() {
    currentIndex++;

    if (currentIndex >= images.length) {
        currentIndex = 0;
    }

    const bannerImg = document.getElementById("bannerImg");

    bannerImg.src = images[currentIndex];
}

setInterval(changeImage, 3000);
