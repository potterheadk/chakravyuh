
    <script>
        // Create floating shapes
        const shapesContainer = document.getElementById('shapes');
        const numberOfShapes = 15;

        for (let i = 0; i < numberOfShapes; i++) {
            const shape = document.createElement('div');
            shape.className = 'shape';

            // Random size between 50 and 200
            const size = Math.random() * 150 + 50;
            shape.style.width = `${size}px`;
            shape.style.height = `${size}px`;

            // Random position
            shape.style.left = `${Math.random() * 100}%`;
            shape.style.top = `${Math.random() * 100}%`;

            shapesContainer.appendChild(shape);
        }

        // Animate shapes with GSAP
        document.querySelectorAll('.shape').forEach(shape => {
            gsap.to(shape, {
                x: 'random(-100, 100)',
                y: 'random(-100, 100)',
                duration: 'random(10, 20)',
                repeat: -1,
                yoyo: true,
                ease: 'none'
            });
        });

        // Parallax effect on scroll
        window.addEventListener('scroll', () => {
            const shapes = document.querySelectorAll('.shape');
            const scrolled = window.pageYOffset;

            shapes.forEach((shape, index) => {
                const speed = 0.2 + (index * 0.1);
                const yPos = -(scrolled * speed);
                shape.style.transform = `translateY(${yPos}px)`;
            });
        });

        // Smooth scroll for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });
    </script>