/**
 * globals.js - Глобальные переменные и функции
 * 
 * Этот файл содержит глобальные переменные и функции,
 * которые должны быть доступны для всех модулей.
 */

// Текущие данные пользователя
window.userAcademicInfo = window.userAcademicInfo || {};
window.userCertificates = window.userCertificates || [];
window.currentSkills = window.currentSkills || [];

// Объявляем глобальные функции для взаимодействия с HTML
window.showUploadModal = function () {
    const modal = document.getElementById('uploadModal');
    if (modal) modal.classList.add('modal-open');
};

window.closeUploadModal = function () {
    const modal = document.getElementById('uploadModal');
    if (modal) {
        modal.classList.remove('modal-open');
        document.getElementById('certificateForm').reset();
        document.getElementById('previewContainer').classList.add('hidden');
    }
};

window.previewCertificate = function (input) {
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
};

window.previewImage = function (input) {
    const preview = document.getElementById('avatarPreview');
    const file = input.files[0];
    const reader = new FileReader();

    reader.onloadend = function () {
        preview.src = reader.result;
    }

    if (file) {
        reader.readAsDataURL(file);
    }
};

window.copyProfileLink = function () {
    const username = document.querySelector('meta[name="current-username"]')?.content;
    if (!username) return;

    const profileLink = window.location.origin + '/' + username;
    navigator.clipboard.writeText(profileLink).then(() => {
        showNotification('Profile link copied to clipboard!');
    }).catch(err => {
        showNotification('Failed to copy link', 'error');
    });
};

// Функции для добавления и удаления языков
window.addLanguage = function () {
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
};

window.removeLanguage = function (button) {
    const languageRow = button.closest('div');
    if (languageRow) {
        languageRow.remove();
    }
};

// Функции для добавления и удаления достижений
window.addAchievement = function () {
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
};

window.removeAchievement = function (button) {
    const achievementRow = button.closest('.p-6');
    if (achievementRow) {
        achievementRow.remove();
    }
};

// Функции для навыков
window.showSkillsEditor = function (e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    const modal = document.getElementById('skillsModal');
    const skillsList = document.getElementById('skillsList');
    if (!modal || !skillsList) return;

    // Очищаем список навыков
    skillsList.innerHTML = '';

    // Добавляем текущие навыки
    window.currentSkills.forEach(skill => addSkillInput(skill));

    // Показываем модальное окно
    modal.classList.add('modal-open');
};

window.closeSkillsModal = function (e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    const modal = document.getElementById('skillsModal');
    if (modal) {
        modal.classList.remove('modal-open');
    }
};

window.addNewSkill = function (e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    addSkillInput();
};

function addSkillInput(value = '') {
    const skillsList = document.getElementById('skillsList');
    if (!skillsList) return;

    const skillDiv = document.createElement('div');
    skillDiv.className = 'flex items-center gap-2 mb-2';

    // Создаем элемент ввода
    const input = document.createElement('input');
    input.className = 'input input-bordered flex-1';
    input.type = 'text';
    input.placeholder = 'Enter skill (e.g., Python, C++)';
    input.maxLength = 20;
    if (value) {
        input.value = value;
    }

    // Создаем кнопку удаления
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-ghost btn-sm text-red-500 hover:bg-red-50';
    removeBtn.textContent = 'Remove';
    removeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        skillDiv.remove();
    });

    // Добавляем элементы в блок
    skillDiv.appendChild(input);
    skillDiv.appendChild(removeBtn);
    skillsList.appendChild(skillDiv);

    // Фокусируемся на новом поле ввода
    input.focus();
}

window.saveSkills = async function (e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    const inputs = document.querySelectorAll('#skillsList input');
    const skills = Array.from(inputs)
        .map(input => input.value.trim())
        .filter(skill => skill !== '');

    try {
        const response = await fetch('/update-skills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ skills })
        });

        const data = await response.json();
        if (data.success) {
            // Обновляем глобальный массив навыков
            window.currentSkills = skills;

            // Обновляем отображение
            updateSkillsDisplay();

            // Закрываем модальное окно
            closeSkillsModal();

            // Обновляем сайдбар рекомендаций, если он виден
            if (typeof isRecommendationsSidebarVisible === 'function' && isRecommendationsSidebarVisible()) {
                const profileData = typeof collectProfileData === 'function' ?
                    collectProfileData() : { personal: { skills: skills } };

                typeof updateRecommendationSidebar === 'function' &&
                    updateRecommendationSidebar(profileData);
            }

            showNotification('Skills updated successfully');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        showNotification('Failed to update skills', 'error');
        console.error('Error:', error);
    }
};

function updateSkillsDisplay() {
    const container = document.getElementById('skillsContainer');
    if (!container) return;

    container.innerHTML = window.currentSkills.map(skill => `
        <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
            ${skill}
        </span>
    `).join('');
}

// Функции для сертификатов
window.deleteCertificate = function (certId) {
    document.getElementById('certificateToDelete').value = certId;
    const modal = document.getElementById('deleteCertificateModal');
    if (modal) {
        modal.classList.add('modal-open');
    }
};

window.closeDeleteCertificateModal = function () {
    const modal = document.getElementById('deleteCertificateModal');
    if (modal) {
        modal.classList.remove('modal-open');
    }
};

// Функции для проектов
window.showCreateProjectModal = function () {
    document.getElementById('projectModalTitle').textContent = 'Create New Project';
    document.getElementById('projectForm').reset();
    document.getElementById('projectId').value = '';

    // Сбрасываем глобальные переменные
    window.currentProjectId = null;
    window.projectImages = [];
    window.projectCollaborators = [];
    window.projectTags = [];
    window.projectThumbnail = null;
    window.projectHeader = null;

    // Сбрасываем изображения предпросмотра
    document.getElementById('thumbnailPreview').src = '/static/placeholder.png';
    document.getElementById('headerPreview').src = '/static/placeholder-wide.png';
    document.getElementById('thumbnailPreviewContainer').classList.remove('border-purple-500');
    document.getElementById('headerPreviewContainer').classList.remove('border-purple-500');

    // Очищаем элементы интерфейса
    document.getElementById('imagesContainer').innerHTML = '';
    document.getElementById('collaboratorsContainer').innerHTML = '';
    document.getElementById('tagsContainer').innerHTML = '';

    // Показываем модальное окно
    document.getElementById('projectModal').classList.add('modal-open');
};

window.closeProjectModal = function () {
    document.getElementById('projectModal').classList.remove('modal-open');
};

window.closeDeleteProjectModal = function () {
    document.getElementById('deleteProjectModal').classList.remove('modal-open');
};

window.previewThumbnail = function (input) {
    const preview = document.getElementById('thumbnailPreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            document.getElementById('thumbnailPreviewContainer').classList.add('border-purple-500');

            // Сохраняем файл миниатюры для последующей загрузки
            window.projectThumbnail = input.files[0];
        };
        reader.readAsDataURL(input.files[0]);
    }
};

window.previewHeader = function (input) {
    const preview = document.getElementById('headerPreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            document.getElementById('headerPreviewContainer').classList.add('border-purple-500');

            // Сохраняем файл заголовка для последующей загрузки
            window.projectHeader = input.files[0];
        };
        reader.readAsDataURL(input.files[0]);
    }
};

window.previewProjectImages = function (input) {
    const imagesContainer = document.getElementById('imagesContainer');

    if (input.files && input.files.length > 0) {
        for (let i = 0; i < input.files.length; i++) {
            const file = input.files[i];

            // Создаем новый ридер для каждого файла
            const reader = new FileReader();
            reader.onload = function (e) {
                const imagePreview = document.createElement('div');
                imagePreview.className = 'relative group';
                imagePreview.innerHTML = `
                    <img src="${e.target.result}" alt="Project Image" 
                        class="w-full h-32 object-cover rounded-lg">
                    <div class="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <button type="button" class="p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                            onclick="removeImagePreview(this)">
                            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                `;

                imagesContainer.appendChild(imagePreview);

                // Сохраняем файл для последующей загрузки
                window.projectImages = window.projectImages || [];
                window.projectImages.push({
                    file: file,
                    preview: e.target.result
                });
            };

            reader.readAsDataURL(file);
        }
    }
};

window.removeImagePreview = function (button) {
    const previewElement = button.closest('.relative');
    const index = Array.from(previewElement.parentNode.children).indexOf(previewElement);

    if (index !== -1) {
        window.projectImages.splice(index, 1);
        previewElement.remove();
    }
};

window.removeExistingImage = function (button, imageUrl) {
    const previewElement = button.closest('.relative');
    const index = Array.from(previewElement.parentNode.children).indexOf(previewElement);

    if (index !== -1) {
        window.projectImages.splice(index, 1);
        previewElement.remove();
    }
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    // Инициализация массива навыков из DOM
    const skillsContainer = document.getElementById('skillsContainer');
    if (skillsContainer) {
        // Получаем навыки из интерфейса
        window.currentSkills = Array.from(skillsContainer.querySelectorAll('span'))
            .map(span => span.textContent.trim());
    }

    console.log("Глобальные переменные и функции загружены");
});