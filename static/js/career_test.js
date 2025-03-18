// Improved career_test.js with better handling and animations

document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on a career test question page
    const questionForm = document.getElementById('questionForm');
    if (!questionForm) return;

    // Handle option selection with visual feedback
    const setupOptionHandlers = () => {
        // Handle radio button selection
        document.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', function () {
                // Remove selected class from all options in the same group
                const name = this.getAttribute('name');
                document.querySelectorAll(`input[name="${name}"] + label`).forEach(label => {
                    label.classList.remove('selected-option');
                });

                // Add selected class to the chosen option
                const label = document.querySelector(`label[for="${this.id}"]`);
                if (label) {
                    label.classList.add('selected-option');
                }

                // Enable the Next button if it was disabled
                const nextButton = document.querySelector('button[name="action"][value="next"]');
                if (nextButton && nextButton.disabled) {
                    nextButton.disabled = false;
                    nextButton.classList.remove('opacity-50', 'cursor-not-allowed');
                }
            });
        });

        // Handle checkbox selection
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', function () {
                const label = document.querySelector(`label[for="${this.id}"]`);
                if (label) {
                    if (this.checked) {
                        label.classList.add('selected-option');
                    } else {
                        label.classList.remove('selected-option');
                    }
                }
            });
        });
    };

    // Set up option handlers on page load
    setupOptionHandlers();

    // Handle form submission via AJAX
    questionForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Show loading indicator
        const submitButton = document.activeElement;
        const originalText = submitButton.innerHTML;
        submitButton.disabled = true;

        // Different loading UI depending on which button was clicked
        if (submitButton.value === 'next') {
            submitButton.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Далее...
            `;
        } else {
            submitButton.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Назад...
            `;
        }

        // Get form data
        const formData = new FormData(questionForm);
        const action = submitButton.value;
        formData.append('action', action);

        // Send AJAX request
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.redirect) {
                    // Smooth transition to the next page
                    document.body.style.opacity = '0';
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 300);
                } else if (data.html) {
                    // Update the question content without reloading
                    const contentContainer = document.getElementById('questionContainer');

                    // Fade out current content
                    contentContainer.style.opacity = '0';

                    // After fade out, update content
                    setTimeout(() => {
                        contentContainer.innerHTML = data.html;

                        // Fade in new content
                        setTimeout(() => {
                            contentContainer.style.opacity = '1';

                            // Re-initialize UI elements
                            setupOptionHandlers();

                            // Scroll to top of question if needed
                            window.scrollTo({
                                top: document.querySelector('.max-w-4xl').offsetTop - 20,
                                behavior: 'smooth'
                            });
                        }, 50);
                    }, 300);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка. Пожалуйста, попробуйте еще раз.');

                // Reset button
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            });
    });
});