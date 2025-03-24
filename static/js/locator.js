// Locate nearby pharmacy
  document.getElementById("locatePharmacyBtn").addEventListener("click", function (event) {
    event.preventDefault(); // Prevent form submission if inside a form

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          window.open(
            `https://www.google.com/maps/search/pharmacy/@${lat},${lng},15z`,
            "_blank"
          );
        },
        (error) => {
          console.error("Geolocation error:", error);
          alert("Unable to retrieve your location. Please enable location services or search manually.");
          window.open(
            "https://www.google.com/maps/search/pharmacy+near+me",
            "_blank"
          );
        }
      );
    } else {
      alert("Geolocation is not supported by your browser. Searching for pharmacies near you.");
      window.open(
        "https://www.google.com/maps/search/pharmacy+near+me",
        "_blank"
      );
    }
  });

  // Create vector background elements
  const vectorBg = document.getElementById("vector-bg");
  const shapes = [
    "M0 0 L20 20", // Lines
    "M0 0 A10 10 0 0 1 20 20", // Curves
    "M0 0 H20 V20", // Right angles
  ];

  for (let i = 0; i < 30; i++) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "vector-element");
    svg.setAttribute("width", "40");
    svg.setAttribute("height", "40");
    svg.setAttribute("viewBox", "0 0 40 40");

    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", shapes[Math.floor(Math.random() * shapes.length)]);
    svg.appendChild(path);

    svg.style.left = `${Math.random() * 100}%`;
    svg.style.top = `${Math.random() * 100}%`;
    svg.style.transform = `rotate(${Math.random() * 360}deg)`;

    vectorBg.appendChild(svg);

    // Animate each vector element
    gsap.to(svg, {
      rotation: "random(-180, 180)",
      x: "random(-30, 30)",
      y: "random(-30, 30)",
      duration: "random(15, 30)",
      repeat: -1,
      yoyo: true,
      ease: "none",
    });
  }

  // Subtle parallax effect on mouse move
  document.addEventListener("mousemove", (e) => {
    const mouseX = e.clientX / window.innerWidth - 0.5;
    const mouseY = e.clientY / window.innerHeight - 0.5;

    gsap.to(".vector-element", {
      x: mouseX * 30,
      y: mouseY * 30,
      duration: 1,
    });
  });