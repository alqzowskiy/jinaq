/**
 * profile.js - Управление профилем и редактирование
 * 
 * Этот файл содержит функции для:
 * - Управления профилем пользователя
 * - Загрузки аватара и обложки
 * - Отправки форм профиля
 * - Управления ссылками
 */

// ===== Глобальные переменные =====
let currentHeaderFile = null;
let headerEditor = {
    verticalPos: 50,
    horizontalPos: 50
};

// ===== Обработчики событий профиля =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('Profile JavaScript загружен');

    // Инициализация обработчиков форм
    initProfileForm();

    // Настройка загрузки аватара
    setupAvatarUpload();

    // Настройка загрузки заголовка
    setupHeaderUpload();

    // Настройка управления ссылками
    setupLinksManagement();
});

// ===== Функции для управления профилем =====

// Инициализация формы профиля
function initProfileForm() {
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        // Обработчик отправки формы профиля
        profileForm.addEventListener('submit', handleProfileSubmit);

        // Настройка сохранения без перезагрузки
        setupFormAjaxSubmission();
    }
}

// Обработчик отправки формы профиля
async function handleProfileSubmit(e) {
    e.preventDefault();

    try {
        const formData = new FormData(this);

        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        const data = await response.json();

        if (data.success) {
            // Обновляем отображаемую информацию без перезагрузки
            updateProfileDisplayInfo(data.user_data);
            showNotification('Profile updated successfully');
        } else {
            throw new Error(data.error || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showNotification('Failed to update profile', 'error');
    }
}

// Настройка сохранения формы без перезагрузки
function setupFormAjaxSubmission() {
    const floatingSaveBtn = document.getElementById('floatingSaveBtn');
    if (floatingSaveBtn) {
        floatingSaveBtn.addEventListener('click', async function (e) {
            e.preventDefault();

            try {
                // Show saving state
                this.disabled = true;
                this.innerHTML = `
                    <div class="save-btn-content">
                        <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Saving...</span>
                    </div>
                `;

                // Save all forms without page reload
                const results = await Promise.all([
                    saveProfileForm(),
                    saveAcademicPortfolio(),
                    saveLinks()
                ]);

                // Check if all operations were successful
                const allSuccessful = results.every(result => result.success);

                if (allSuccessful) {
                    showNotification('All changes successfully saved');

                    // Update display sections without reloading
                    updateDisplaySections(results[0].user_data);
                } else {
                    // Find error message from failed operation
                    const errorMessage = results.find(result => !result.success)?.error || 'An error occurred';
                    showNotification('Error saving changes: ' + errorMessage, 'error');
                }

                // Restore button state
                this.disabled = false;
                this.innerHTML = `
                    <div class="save-btn-content">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Save All Changes</span>
                    </div>
                `;

            } catch (error) {
                console.error('Error saving changes:', error);
                showNotification('Error saving changes: ' + error.message, 'error');

                // Restore button state
                this.disabled = false;
                this.innerHTML = `
                    <div class="save-btn-content">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                        <span>Save All Changes</span>
                    </div>
                `;
            }
        });
    }
}

// Сохранение формы профиля
async function saveProfileForm() {
    const profileForm = document.getElementById('profileForm');
    if (!profileForm) return { success: false };

    // Create FormData from the form
    const formData = new FormData(profileForm);

    try {
        // Show loading state or spinner here if needed

        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            // Update the UI with new data without reloading
            updateProfileDisplayInfo(data.user_data || {});
            showNotification('Profile successfully updated');
            return data;
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        showNotification('Failed to save profile: ' + error.message, 'error');
        return { success: false, error: error.message };
    }
}

// Обновление секций отображения
function updateDisplaySections() {
    // Обновление информации профиля
    updateProfileInfo();

    // Обновление отображения навыков
    updateSkillsDisplay();
}

// Обновление отображаемой информации профиля
function updateProfileInfo() {
    const profileForm = document.getElementById('profileForm');
    const displayInfo = document.getElementById('profileDisplayInfo');
    if (!profileForm || !displayInfo) return;

    // Получаем значения из формы
    const fullName = profileForm.querySelector('input[name="full_name"]')?.value || '';
    const specialty = profileForm.querySelector('input[name="specialty"]')?.value || '';
    const age = profileForm.querySelector('input[name="age"]')?.value || '';
    const goals = profileForm.querySelector('textarea[name="goals"]')?.value || '';
    const bio = profileForm.querySelector('textarea[name="bio"]')?.value || '';
    const education = profileForm.querySelector('textarea[name="education"]')?.value || '';

    // Обновляем имя профиля в карточке
    const profileName = document.querySelector('.gradient-text');
    if (profileName && fullName) {
        profileName.textContent = fullName;
    }

    // Создаем HTML для отображения
    let html = `<h2 class="text-2xl font-bold mb-6">Profile Information</h2><div class="space-y-4">`;

    if (specialty) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Specialty</h3>
            <p class="text-gray-900">${specialty}</p>
        </div>`;
    }

    if (age) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Age</h3>
            <p class="text-gray-900">${age} years</p>
        </div>`;
    }

    if (goals) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Goals</h3>
            <p class="text-gray-900">${goals}</p>
        </div>`;
    }

    if (bio) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Bio</h3>
            <p class="text-gray-900">${bio}</p>
        </div>`;
    }

    // Добавляем навыки, если они есть
    if (window.currentSkills && window.currentSkills.length > 0) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Skills</h3>
            <div class="flex flex-wrap gap-2 mt-2">`;

        window.currentSkills.forEach(skill => {
            html += `
            <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                ${skill}
            </span>`;
        });

        html += `</div></div>`;
    }

    if (education) {
        html += `
        <div>
            <h3 class="font-medium text-gray-700">Education</h3>
            <p class="text-gray-900">${education}</p>
        </div>`;
    }

    html += `</div>`;
    displayInfo.innerHTML = html;
}

// ===== Функции для аватара =====

// Настройка загрузки аватара
function setupAvatarUpload() {
    const avatarInput = document.querySelector('input[name="avatar"]');
    if (avatarInput) {
        avatarInput.addEventListener('change', handleAvatarUpload);
    }
}

// Обработчик загрузки аватара
async function handleAvatarUpload(event) {
    const file = this.files[0];
    if (!file) return;

    // Сразу предварительно отображаем изображение
    const preview = document.getElementById('avatarPreview');
    if (preview) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    // Загружаем аватар на сервер
    const formData = new FormData();
    formData.append('avatar', file);

    try {
        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });

        const data = await response.json();

        if (data.success) {
            // Обновляем все экземпляры аватара на странице
            document.querySelectorAll('.avatar img').forEach(img => {
                img.src = data.avatar_url;
            });

            showNotification('Avatar successfully updated');
        } else {
            throw new Error(data.error || 'Failed to update avatar');
        }
    } catch (error) {
        console.error('Avatar update error:', error);
        showNotification('Avatar update error', 'error');
    }
}

// Предварительный просмотр изображения
function previewImage(input) {
    const preview = document.getElementById('avatarPreview');
    const file = input.files[0];
    const reader = new FileReader();

    reader.onloadend = function () {
        preview.src = reader.result;
    };

    if (file) {
        reader.readAsDataURL(file);
    } else {
        preview.src = "{{ avatar_url }}";
    }
}

// ===== Функции для заголовка (шапки) профиля =====

// Настройка загрузки заголовка
function setupHeaderUpload() {
    const headerInput = document.getElementById('headerInput');
    if (headerInput) {
        headerInput.addEventListener('change', function (e) {
            handleHeaderUpload(this);
        });
    }
}

// Обработчик загрузки заголовка
function handleHeaderUpload(input) {
    if (!input.files || !input.files[0]) return;

    const file = input.files[0];

    // Проверка размера и типа файла
    if (file.size > 5 * 1024 * 1024) {
        showNotification('File size must be less than 5MB', 'error');
        return;
    }

    if (!file.type.startsWith('image/')) {
        showNotification('Only images can be uploaded', 'error');
        return;
    }

    // Создаем FormData и обновляем заголовок
    const formData = new FormData();
    formData.append('header_image', file);
    formData.append('position', '50% 50%'); // Позиция по умолчанию

    fetch('/update_header', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Обновляем изображение заголовка
                const headerImage = document.getElementById('headerImage');
                headerImage.src = data.header.url;
                headerImage.style.objectPosition = data.header.position;

                showNotification('The title has been updated successfully.');
            } else {
                throw new Error(data.error || 'Failed to update title');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Failed to update header image', 'error');
        });
}

// Обновление позиции заголовка
function updateHeaderPreviewPosition() {
    const xSlider = document.getElementById('xPosition');
    const ySlider = document.getElementById('yPosition');

    if (!xSlider || !ySlider) return;

    const x = xSlider.value;
    const y = ySlider.value;

    const desktopPreview = document.getElementById('desktopHeaderPreview');
    const mobilePreview = document.getElementById('mobileHeaderPreview');

    if (desktopPreview) desktopPreview.style.objectPosition = `${x}% ${y}%`;
    if (mobilePreview) mobilePreview.style.objectPosition = `${x}% ${y}%`;

    // Обновляем сохраненные значения
    headerEditor.horizontalPos = x;
    headerEditor.verticalPos = y;
}

// ===== Функции для управления ссылками =====

// Настройка управления ссылками
function setupLinksManagement() {
    // Добавляем глобальные функции для взаимодействия с HTML
    window.addLink = addLink;
    window.removeLink = removeLink;
}

// Добавление новой ссылки
function addLink() {
    const linksContainer = document.getElementById('linksContainer');
    if (!linksContainer) return;

    const linkEntry = document.createElement('div');
    linkEntry.className = 'link-entry group p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-all duration-200';
    linkEntry.innerHTML = `
        <div class="flex items-start gap-4">
            <div class="link-icon flex-shrink-0 mt-2">
                <svg class="h-8 w-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
            </div>
            <div class="flex-grow space-y-3">
                <input type="text" name="link_titles[]" placeholder="Link Title"
                    class="input input-bordered w-full bg-white focus:ring-2 focus:ring-black transition-all">
                <input type="text" name="link_urls[]" placeholder="URL"
                    class="input input-bordered w-full bg-white focus:ring-2 focus:ring-black transition-all">
            </div>
            <div class="flex-shrink-0 flex items-start space-x-2">
                <button type="button" onclick="removeLink(this)"
                    class="btn btn-ghost btn-sm p-2 hover:bg-red-50 text-red-500 transition-colors rounded-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none"
                        viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        </div>
    `;

    linksContainer.appendChild(linkEntry);
}

// Удаление ссылки
function removeLink(button) {
    const linkEntry = button.closest('.link-entry');
    if (linkEntry) {
        linkEntry.remove();
    }
}

// Сохранение ссылок

async function saveLinks() {
    const linkTitles = Array.from(document.querySelectorAll('input[name="link_titles[]"]'))
        .map(input => input.value.trim());
    const linkUrls = Array.from(document.querySelectorAll('input[name="link_urls[]"]'))
        .map(input => input.value.trim());

    const links = linkTitles.map((title, index) => ({
        title: title,
        url: linkUrls[index]
    })).filter(link => link.title && link.url);

    try {
        // Show loading state if needed

        const response = await fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                action: 'update_links',
                links: links
            })
        });

        if (!response.ok) {
            throw new Error(`Server responded with status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            showNotification('Links successfully updated');
            return data;
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    } catch (error) {
        console.error('Error saving links:', error);
        showNotification('Failed to save links: ' + error.message, 'error');
        return { success: false, error: error.message };
    }
}
function updateProfileDisplayInfo(userData) {
    // Update display name in the profile card
    const profileName = document.querySelector('.gradient-text');
    if (profileName && userData.full_name) {
        profileName.textContent = userData.full_name;
    }

    // Update username
    const usernameElement = document.querySelector('p.text-gray-600');
    if (usernameElement && userData.username) {
        usernameElement.innerHTML = usernameElement.innerHTML.replace(
            /@[^<]+/,
            '@' + (userData.display_username || userData.username)
        );
    }

    // Update profile display info
    const displayInfo = document.getElementById('profileDisplayInfo');
    if (displayInfo) {
        let html = `<h2 class="text-2xl font-bold mb-6">Profile Information</h2><div class="space-y-4">`;

        if (userData.specialty) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Specialty</h3>
                <p class="text-gray-900">${userData.specialty}</p>
            </div>`;
        }

        if (userData.age) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Age</h3>
                <p class="text-gray-900">${userData.age} years</p>
            </div>`;
        }

        if (userData.goals) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Goals</h3>
                <p class="text-gray-900">${userData.goals}</p>
            </div>`;
        }

        if (userData.bio) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Bio</h3>
                <p class="text-gray-900">${userData.bio}</p>
            </div>`;
        }

        // Add skills section if skills exist
        if (userData.skills && userData.skills.length > 0) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Skills</h3>
                <div class="flex flex-wrap gap-2 mt-2">`;

            userData.skills.forEach(skill => {
                html += `
                <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                    ${skill}
                </span>`;
            });

            html += `</div></div>`;
        }

        if (userData.education) {
            html += `
            <div>
                <h3 class="font-medium text-gray-700">Education</h3>
                <p class="text-gray-900">${userData.education}</p>
            </div>`;
        }

        html += `</div>`;
        displayInfo.innerHTML = html;
    }
}