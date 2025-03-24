// BMI Calculator
        document.getElementById('bmiForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const weight = parseFloat(document.getElementById('weight').value);
            const height = parseFloat(document.getElementById('height').value);

            try {
                const response = await fetch('/calculate_bmi', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ weight, height }),
                });

                const data = await response.json();
                const resultDiv = document.getElementById('bmiResult');
                resultDiv.style.display = 'block';
                resultDiv.textContent = data.bmi;
            } catch (error) {
                console.error('Error:', error);
            }
        });

        // Diabetes Risk Assessment
        document.getElementById('diabetesForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const loading = document.getElementById('diabetesLoading');
            const resultDiv = document.getElementById('diabetesResult');

            loading.style.display = 'block';
            resultDiv.style.display = 'none';

            const data = {
                pregnancies: parseInt(document.getElementById('pregnancies').value),
                glucose: parseInt(document.getElementById('glucose').value),
                blood_pressure: parseInt(document.getElementById('bloodPressure').value),
                skin_thickness: parseInt(document.getElementById('skinThickness').value),
                insulin: parseInt(document.getElementById('insulin').value),
                bmi: parseFloat(document.getElementById('bmi').value),
                diabetes_pedigree: parseFloat(document.getElementById('diabetesPedigree').value),
                age: parseInt(document.getElementById('age').value)
            };

            try {
                const response = await fetch('/predict_diabetes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                const result = await response.json();
                loading.style.display = 'none';
                resultDiv.style.display = 'block';
                resultDiv.textContent = result.prediction;
            } catch (error) {
                console.error('Error:', error);
                loading.style.display = 'none';
            }
        });

        // Heart Disease Risk Assessment
        document.getElementById('heartDiseaseForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const loading = document.getElementById('heartDiseaseLoading');
            const resultDiv = document.getElementById('heartDiseaseResult');

            loading.style.display = 'block';
            resultDiv.style.display = 'none';

            const data = {
                age: parseInt(document.getElementById('hdAge').value),
                cholesterol: parseInt(document.getElementById('cholesterol').value),
                blood_pressure: parseInt(document.getElementById('hdBloodPressure').value),
                exercise: parseFloat(document.getElementById('exercise').value)
            };

            try {
                const response = await fetch('/predict_heart_disease', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data),
                });

                const result = await response.json();
                loading.style.display = 'none';
                resultDiv.style.display = 'block';
                resultDiv.textContent = result.prediction;
            } catch (error) {
                console.error('Error:', error);
                loading.style.display = 'none';
            }
        });