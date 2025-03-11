/**
 * academic.js - Академическое портфолио
 * 
 * Этот файл содержит функции для управления:
 * - Академическим портфолио
 * - Языками
 * - Достижениями
 * - Сертификатами
 */

// ===== Обработчики событий академического портфолио =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('Academic JavaScript загружен');

    // Инициализация академического портфолио
    initAcademicPortfolio();

    // Настройка управления сертификатами
    setupCertificateHandling();
});
// Use event delegation for certificate checkboxes

// ===== Функции для академического портфолио =====

// Инициализация академического портфолио
function initAcademicPortfolio() {
    const academicForm = document.getElementById('academicPortfolioForm');
    if (academicForm) {
        // Устанавливаем обработчики для кнопок добавления языка и достижений
        setupLanguageHandlers();
        setupAchievementHandlers();

        // Настройка отправки формы академического портфолио
        setupAcademicFormSubmission();
    }
}

// Настройка обработчиков для языков
// In academic.js, modify setupLanguageHandlers function
function setupLanguageHandlers() {
    const addLanguageBtn = document.getElementById('addLanguageBtn');
    if (addLanguageBtn) {
        // First, remove any existing event listeners by cloning the button
        const newBtn = addLanguageBtn.cloneNode(true);
        addLanguageBtn.parentNode.replaceChild(newBtn, addLanguageBtn);

        // Then add a single event listener
        newBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            addLanguage();
        });
    }

    // Ensure global functions are properly defined
    window.addLanguage = addLanguage;
    window.removeLanguage = removeLanguage;
}

// Настройка обработчиков для достижений
// In academic.js, modify setupAchievementHandlers function
function setupAchievementHandlers() {
    const addAchievementBtn = document.getElementById('addAchievementBtn');
    if (addAchievementBtn) {
        // First, remove any existing event listeners by cloning the button
        const newBtn = addAchievementBtn.cloneNode(true);
        addAchievementBtn.parentNode.replaceChild(newBtn, addAchievementBtn);

        // Then add a single event listener
        newBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            addAchievement();
        });
    }

    // Ensure global functions are properly defined
    window.addAchievement = addAchievement;
    window.removeAchievement = removeAchievement;
}
// Настройка отправки формы академического портфолио
function setupAcademicFormSubmission() {
    const academicForm = document.getElementById('academicPortfolioForm');
    if (academicForm) {
        academicForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            await saveAcademicPortfolio();
        });
    }
}

// Сохранение академического портфолио
async function saveAcademicPortfolio() {
    const academicForm = document.getElementById('academicPortfolioForm');
    if (!academicForm) return { success: false };

    // Collect data from the form
    const academicData = {
        gpa: academicForm.querySelector('input[name="gpa"]')?.value || '',
        sat_score: academicForm.querySelector('input[name="sat_score"]')?.value || '',
        toefl_score: academicForm.querySelector('input[name="toefl_score"]')?.value || '',
        ielts_score: academicForm.querySelector('input[name="ielts_score"]')?.value || '',
        languages: collectLanguages(),
        achievements: collectAchievements()
    };

    try {
        // Show loading state if needed

        const response = await fetch('/update_academic_portfolio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(academicData)
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {

            return data;
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error saving academic portfolio:', error);
        showNotification('Failed to save academic portfolio: ' + error.message, 'error');
        return { success: false, error: error.message };
    }
}

// ===== Функции для языков =====

// Добавление нового языка
function addLanguage() {
    const languagesContainer = document.getElementById('languagesContainer');
    if (!languagesContainer) return;

    const languageRow = document.createElement('div');
    languageRow.className = 'flex gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-all duration-200';
    languageRow.innerHTML = `
        <input type="text" name="language_name" placeholder="Language"
            class="input input-bordered flex-1 bg-white focus:ring-2 focus:ring-black transition-all">
        <select name="language_level"
            class="select select-bordered bg-white focus:ring-2 focus:ring-black transition-all">
            <option value="A1">A1 - Beginner</option>
            <option value="A2">A2 - Elementary</option>
            <option value="B1">B1 - Intermediate</option>
            <option value="B2">B2 - Upper Intermediate</option>
            <option value="C1">C1 - Advanced</option>
            <option value="C2">C2 - Mastery</option>
        </select>
        <button type="button" onclick="removeLanguage(this)"
            class="btn btn-ghost text-red-500 hover:bg-red-50 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
        </button>
    `;

    languagesContainer.appendChild(languageRow);
}

// Удаление языка
function removeLanguage(button) {
    console.log('Removing language element');
    const languageRow = button.closest('.flex.gap-4.p-4');
    if (languageRow) {
        languageRow.remove();
    } else {
        console.error('Could not find language row to remove');
    }
}


// Сбор данных о языках из формы
function collectLanguages() {
    const languages = [];
    const containers = document.querySelectorAll('#languagesContainer > div');

    containers.forEach(container => {
        const nameInput = container.querySelector('input[name="language_name"]');
        const levelSelect = container.querySelector('select[name="language_level"]');

        if (nameInput && nameInput.value.trim()) {
            languages.push({
                name: nameInput.value.trim(),
                level: levelSelect ? levelSelect.value : 'A1'
            });
        }
    });

    return languages;
}

// ===== Функции для достижений =====

// Добавление нового достижения
function addAchievement() {
    const achievementsContainer = document.getElementById('achievementsContainer');
    if (!achievementsContainer) return;

    const achievementRow = document.createElement('div');
    achievementRow.className = 'p-6 bg-gray-50 rounded-xl hover:bg-gray-100 transition-all duration-200';
    achievementRow.innerHTML = `
        <div class="space-y-4">
            <input type="text" name="achievement_title" placeholder="Achievement Title"
                class="input input-bordered w-full bg-white focus:ring-2 focus:ring-black transition-all">
            <textarea name="achievement_description" placeholder="Description"
                class="textarea textarea-bordered w-full bg-white focus:ring-2 focus:ring-black transition-all min-h-[100px]"></textarea>
            <div class="flex items-center justify-between">
                <input type="date" name="achievement_date"
                    class="input input-bordered bg-white focus:ring-2 focus:ring-black transition-all">
                <button type="button" onclick="removeAchievement(this)"
                    class="btn btn-ghost text-red-500 hover:bg-red-50 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                        viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        </div>
    `;

    achievementsContainer.appendChild(achievementRow);
}

// Удаление достижения
function removeAchievement(button) {
    console.log('Removing achievement element');
    const achievementRow = button.closest('.p-6.bg-gray-50');
    if (achievementRow) {
        achievementRow.remove();
    } else {
        console.error('Could not find achievement row to remove');
    }
}

// Сбор данных о достижениях из формы
function collectAchievements() {
    const achievements = [];
    const containers = document.querySelectorAll('#achievementsContainer > div');

    containers.forEach(container => {
        const titleInput = container.querySelector('input[name="achievement_title"]');
        const descTextarea = container.querySelector('textarea[name="achievement_description"]');
        const dateInput = container.querySelector('input[name="achievement_date"]');

        if (titleInput && titleInput.value.trim()) {
            achievements.push({
                title: titleInput.value.trim(),
                description: descTextarea ? descTextarea.value : '',
                date: dateInput ? dateInput.value : ''
            });
        }
    });

    return achievements;
}

// ===== Функции для сертификатов =====

// Настройка управления сертификатами
function setupCertificateHandling() {
    // Добавляем глобальные функции для взаимодействия с HTML
    window.showUploadModal = showUploadModal;
    window.closeUploadModal = closeUploadModal;
    window.previewCertificate = previewCertificate;
    window.deleteCertificate = deleteCertificate;
    window.closeDeleteCertificateModal = closeDeleteCertificateModal;




}

// Отображение модального окна загрузки
function showUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.add('modal-open');
    }
}

// Закрытие модального окна загрузки
function closeUploadModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.remove('modal-open');
        document.getElementById('certificateForm').reset();
        document.getElementById('previewContainer').classList.add('hidden');
    }
}

// Предварительный просмотр сертификата
function previewCertificate(input) {
    const previewContainer = document.getElementById('previewContainer');
    const imagePreview = document.getElementById('imagePreview');

    if (input.files && input.files[0]) {
        const file = input.files[0];
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                imagePreview.src = e.target.result;
                previewContainer.classList.remove('hidden');
            }
            reader.readAsDataURL(file);
        } else {
            previewContainer.classList.add('hidden');
        }
    }
}

// Удаление сертификата с подтверждением
function deleteCertificate(certId) {
    console.log('Attempting to delete certificate:', certId);
    document.getElementById('certificateToDelete').value = certId;
    const modal = document.getElementById('deleteCertificateModal');
    if (modal) {
        modal.classList.add('modal-open');
    }

    // Make sure the confirmation button has a working event listener
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (confirmBtn) {
        // Remove any existing listeners to prevent duplicates
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

        newBtn.addEventListener('click', function () {
            console.log('Delete confirmation clicked for certificate:', certId);
            performCertificateDelete(certId);
        });
    }
}


// Закрытие модального окна подтверждения удаления


// Выполнение удаления сертификата
// Update the performCertificateDelete function in academic.js
async function performCertificateDelete(certId) {
    try {
        console.log('Performing certificate deletion for:', certId);
        const response = await fetch(`/delete-certificate/${certId}`, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const contentType = response.headers.get('content-type');
        let result;

        if (contentType && contentType.includes('application/json')) {
            result = await response.json();
        } else {
            // Handle non-JSON response
            const text = await response.text();
            result = { status: response.ok ? 'success' : 'error', text: text };
        }

        if (response.ok) {
            // Find and remove the certificate from the UI
            const certCard = document.querySelector(`.group[data-cert-id="${certId}"]`) ||
                document.querySelector(`.bg-gray-50[data-cert-id="${certId}"]`);

            if (certCard) {
                certCard.remove();
                console.log('Certificate removed from UI');
            } else {
                console.log('Certificate element not found in DOM, reloading page');
                window.location.reload(); // Fallback if we can't find the element
            }

            showNotification('Certificate successfully deleted');
            closeDeleteCertificateModal();
            return true;
        } else {
            throw new Error(result.error || 'Failed to delete certificate');
        }
    } catch (error) {
        console.error('Error deleting certificate:', error);
        showNotification('Failed to delete certificate', 'error');
        return false;
    }
}

// Настройка формы загрузки сертификата
function setupCertificateForm() {
    const certificateForm = document.getElementById('certificateForm');
    if (certificateForm) {
        certificateForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const formData = new FormData();
            const title = document.getElementById('certTitle').value;
            const fileInput = this.querySelector('input[type="file"]');

            if (!fileInput || !fileInput.files || !fileInput.files[0]) {
                showNotification('Please select a file', 'error');
                return;
            }

            formData.append('title', title);
            formData.append('certificate', fileInput.files[0]);

            try {
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                const data = await response.json();

                if (data.success) {
                    showNotification('Certificate uploaded successfully');
                    closeUploadModal();
                    window.location.reload();
                } else {
                    throw new Error(data.error || 'Загрузка не удалась');
                }
            } catch (error) {
                console.error('Ошибка загрузки:', error);
                showNotification('Failed to load certificate', 'error');
            }
        });
    }
}

// Настройка кнопки подтверждения удаления
function setupDeleteConfirmation() {
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            const certId = document.getElementById('certificateToDelete').value;
            if (certId) {
                performCertificateDelete(certId);
                closeDeleteCertificateModal();
            }
        });
    }
}


// Add this to academic.js - Replace the current certificate deletion functions

// Global variable to track selected certificates
let selectedCertificates = [];

// Function to delete a certificate (called when delete button is clicked)
function deleteCertificate(certId) {
    console.log('Opening delete confirmation for certificate:', certId);

    // Set the certificate ID in the hidden field
    const certIdField = document.getElementById('certificateToDelete');
    if (certIdField) {
        certIdField.value = certId;
    }

    // Open the confirmation modal
    const modal = document.getElementById('deleteCertificateModal');
    if (modal) {
        modal.classList.add('modal-open');
    } else {
        console.error('Delete confirmation modal not found');
    }
}

// Function to close the delete confirmation modal
function closeDeleteCertificateModal() {
    const modal = document.getElementById('deleteCertificateModal');
    if (modal) {
        modal.classList.remove('modal-open');
    }
}

// Function to actually perform the certificate deletion
async function performCertificateDelete() {
    // Get the certificate ID from the hidden field
    const certId = document.getElementById('certificateToDelete').value;
    if (!certId) {
        console.error('No certificate ID found');
        return;
    }

    console.log('Deleting certificate:', certId);

    try {
        // Disable the delete button and show loading state
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (deleteBtn) {
            deleteBtn.disabled = true;
            deleteBtn.innerHTML = '<span class="loading loading-spinner loading-sm"></span> Deleting...';
        }

        // Send delete request to the server
        const response = await fetch(`/delete-certificate/${certId}`, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        // Check for errors
        if (!response.ok) {
            throw new Error(`Server error (${response.status})`);
        }

        // Try to parse JSON response
        let result;
        try {
            result = await response.json();
        } catch (e) {
            // If response isn't JSON, create a simple result object
            result = { status: response.ok ? 'success' : 'error' };
        }

        if (response.ok) {
            // Find and remove the certificate from the UI
            const certCard = document.querySelector(`.group[data-cert-id="${certId}"]`);
            if (certCard) {
                certCard.remove();
                console.log('Certificate removed from UI');
            } else {
                console.log('Certificate card not found, reloading page');
                window.location.reload();
                return;
            }

            // Close the modal and show success message
            closeDeleteCertificateModal();
            showNotification('Certificate successfully deleted');

            // If all certificates are deleted, reload to show empty state
            const remainingCerts = document.querySelectorAll('.group[data-cert-id]');
            if (remainingCerts.length === 0) {
                window.location.reload();
            }
        } else {
            throw new Error(result.error || 'Failed to delete certificate');
        }
    } catch (error) {
        console.error('Error deleting certificate:', error);
        showNotification('Failed to delete certificate', 'error');

        // Reset button state
        const deleteBtn = document.getElementById('confirmDeleteBtn');
        if (deleteBtn) {
            deleteBtn.disabled = false;
            deleteBtn.textContent = 'Delete';
        }
    }
}

// Function to set up certificate handling
function setupCertificateHandling() {
    console.log('Setting up certificate handling');

    // Setup global functions
    window.showUploadModal = showUploadModal;
    window.closeUploadModal = closeUploadModal;
    window.previewCertificate = previewCertificate;
    window.deleteCertificate = deleteCertificate;
    window.closeDeleteCertificateModal = closeDeleteCertificateModal;

    // Setup delete confirmation button
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
        // Remove existing event listeners
        const newBtn = confirmDeleteBtn.cloneNode(true);
        confirmDeleteBtn.parentNode.replaceChild(newBtn, confirmDeleteBtn);

        // Add new event listener
        newBtn.addEventListener('click', performCertificateDelete);
        console.log('Delete confirmation button set up');
    } else {
        console.warn('Delete confirmation button not found');
    }

    // Setup certificate form
    setupCertificateForm();

    console.log('Certificate handling setup complete');
}


// API function to delete a single certificate
async function deleteCertificateApi(certId) {
    try {
        console.log('Deleting certificate:', certId);
        const response = await fetch(`/delete-certificate/${certId}`, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`Server error (${response.status})`);
        }

        const result = await response.json();
        return { success: true, id: certId };

    } catch (error) {
        console.error(`Error deleting certificate ${certId}:`, error);
        return { success: false, id: certId, error: error.message };
    }
}

