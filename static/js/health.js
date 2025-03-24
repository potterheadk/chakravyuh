// Vector background animation
const vectorBg = document.getElementById("vector-bg");
const shapes = ["M0 0 L20 20", "M0 0 A10 10 0 0 1 20 20", "M0 0 H20 V20"];

for (let i = 0; i < 50; i++) {
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

// Health form functionality
class HealthForm {
  constructor() {
    this.medications = [];
    this.allergies = [];
    this.setupListeners();
  }

  setupListeners() {
    document
      .getElementById("healthForm")
      .addEventListener("submit", (e) => this.handleSubmit(e));
    document
      .getElementById("medicationInput")
      .addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this.addItem("medication");
        }
      });
    document
      .getElementById("allergyInput")
      .addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this.addItem("allergy");
        }
      });
  }

  addItem(type) {
    const input = document.getElementById(`${type}Input`);
    const value = input.value.trim();

    if (!value) return;

    const items = type === "medication" ? this.medications : this.allergies;
    if (!items.includes(value)) {
      items.push(value);
      this.updateTags(type);
    }

    input.value = "";
  }

  removeItem(type, value) {
    const items = type === "medication" ? this.medications : this.allergies;
    const index = items.indexOf(value);
    if (index > -1) {
      items.splice(index, 1);
      this.updateTags(type);
    }
  }

  updateTags(type) {
    const container = document.getElementById(`${type}Tags`);
    const items = type === "medication" ? this.medications : this.allergies;

    container.innerHTML = items
      .map(
        (item) => `
                    <span class="tag">
                        ${item}
                        <button type="button" onclick="healthForm.removeItem('${type}', '${item}')">×</button>
                    </span>
                `,
      )
      .join("");
  }

  showLoading(show) {
    document.getElementById("loading").style.display = show ? "block" : "none";
  }

  showResult(message, isError = false) {
    const result = document.getElementById("result");
    result.textContent = message;
    result.style.display = "block";
    result.className = isError ? "error" : "success";
  }

  async handleSubmit(e) {
    e.preventDefault();
    this.showLoading(true);

    try {
      const response = await fetch("/correlate_health", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          medications: this.medications,
          allergies: this.allergies,
          genetic_history: document.getElementById("geneticHistory").value,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Analysis failed");
      }

      this.showResult(data.correlation_analysis);
    } catch (error) {
      this.showResult(error.message, true);
    } finally {
      this.showLoading(false);
    }
  }
}

const healthForm = new HealthForm();

// Parallax effect
document.addEventListener("mousemove", (e) => {
  const mouseX = e.clientX / window.innerWidth - 0.5;
  const mouseY = e.clientY / window.innerHeight - 0.5;

  gsap.to(".vector-element", {
    x: mouseX * 30,
    y: mouseY * 30,
    duration: 1,
  });
});
