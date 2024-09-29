<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tag Cloud</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        #tag-cloud-container {
            position: relative;
            width: 90%;
            height: 90%;
            background-color: white;
            overflow: hidden;
        }
        .tag {
            position: absolute;
            transition: transform 0.4s, color 0.4s;
            transform: scale(1); /* Normal size */
        }
        .tag:hover {
            transform: scale(1.5); /* Grow on hover */
            color: gold; /* Change color on hover */
        }
    </style>
</head>
<body>

<div id="tag-cloud-container"></div>

<script>
    async function fetchJsonFromS3() {
        try {
            // Replace the URL below with your S3 JSON file link
            const response = await fetch('${url}');
            const jsonData = await response.json();
            return jsonData;
        } catch (error) {
            console.error('Error fetching JSON:', error);
        }
    }

    function getRandomColor() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    function isOverlapping(wordElement, placedWords) {
        const wordRect = wordElement.getBoundingClientRect();

        for (const placedRect of placedWords) {
            const rect = placedRect.getBoundingClientRect();
            if (!(wordRect.right < rect.left ||
                  wordRect.left > rect.right ||
                  wordRect.bottom < rect.top ||
                  wordRect.top > rect.bottom)) {
                return true;
            }
        }
        return false;
    }

    function createTagCloud(jsonData) {
        const container = document.getElementById('tag-cloud-container');
        const centerX = container.offsetWidth / 2;
        const centerY = container.offsetHeight / 2;
        const radius = Math.min(centerX, centerY) * 0.7;

        const placedWords = [];

        jsonData.forEach((item, index) => {
            const wordElement = document.createElement('span');
            wordElement.textContent = item.value;
            wordElement.classList.add('tag');
            
            wordElement.style.color = getRandomColor();
            wordElement.style.fontSize = `$${item.count * 20}px`;

            let placed = false;
            let attempts = 0;
            while (!placed && attempts < 100) {
                const angle = (Math.random() * Math.PI * 2);
                const distance = Math.random() * radius;

                const x = centerX + distance * Math.cos(angle) - (wordElement.offsetWidth / 2);
                const y = centerY + distance * Math.sin(angle) - (wordElement.offsetHeight / 2);

                wordElement.style.left = `$${x}px`;
                wordElement.style.top = `$${y}px`;
                
                container.appendChild(wordElement);

                if (!isOverlapping(wordElement, placedWords)) {
                    placedWords.push(wordElement);
                    placed = true;
                } else {
                    container.removeChild(wordElement);
                }

                attempts++;
            }
        });
    }

    async function initializeTagCloud() {
        const jsonData = await fetchJsonFromS3();
        if (jsonData) {
            createTagCloud(jsonData);
        }
    }

    window.onload = initializeTagCloud;
</script>

</body>
</html>
