/**
 * projects.js - Проекты пользователя
 * 
 * Этот файл содержит функции для:
 * - Создания и редактирования проектов
 * - Управления сотрудниками проекта
 * - Загрузки изображений проекта
 * - Управления тегами проекта
 */

// ===== Глобальные переменные =====

// Идентификатор текущего проекта
let currentProjectId = null;

// Массивы для хранения данных о проекте
let projectImages = [];
let projectCollaborators = [];
let projectTags = [];
let projectThumbnail = null;
let projectHeader = null;

// Имя текущего пользователя
let currentUsername = '';

// ===== Обработчики событий проектов =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('Projects JavaScript загружен');

    // Получаем имя текущего пользователя из сессии
    const usernameMeta = document.querySelector('meta[name="current-username"]');
    if (usernameMeta) {
        currentUsername = usernameMeta.getAttribute('content');
    }

    // Инициализация функций для проектов
    initProjectFunctions();

    // Настройка формы проекта
    setupProjectForm();

    // Настройка модального окна подтверждения удаления
    setupDeleteConfirmation();
});

// ===== Функции для управления проектами =====

// Инициализация функций для проектов
function initProjectFunctions() {
    // Добавляем глобальные функции для взаимодействия с HTML
    window.showCreateProjectModal = showCreateProjectModal;
    window.closeProjectModal = closeProjectModal;
    window.previewThumbnail = previewThumbnail;
    window.previewHeader = previewHeader;
    window.previewProjectImages = previewProjectImages;
    window.removeImagePreview = removeImagePreview;
    window.removeExistingImage = removeExistingImage;
    window.editProject = editProject;
    window.deleteProject = deleteProject;
    window.closeDeleteProjectModal = closeDeleteProjectModal;
    window.addTag = addTag;
    window.removeTag = removeTag;
    window.searchUsers = searchUsers;
    window.addCollaborator = addCollaborator;
    window.removeCollaborator = removeCollaborator;
}

// Показ модального окна создания проекта
function showCreateProjectModal() {
    document.getElementById('projectModalTitle').textContent = 'Create New Project';
    document.getElementById('projectForm').reset();
    document.getElementById('projectId').value = '';

    // Сбрасываем глобальные переменные
    currentProjectId = null;
    projectImages = [];
    projectCollaborators = [];
    projectTags = [];
    projectThumbnail = null;
    projectHeader = null;

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
}

// Закрытие модального окна проекта
function closeProjectModal() {
    document.getElementById('projectModal').classList.remove('modal-open');
}

// Предварительный просмотр миниатюры
function previewThumbnail(input) {
    const preview = document.getElementById('thumbnailPreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            document.getElementById('thumbnailPreviewContainer').classList.add('border-purple-500');

            // Сохраняем файл миниатюры для последующей загрузки
            projectThumbnail = input.files[0];
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Предварительный просмотр заголовка
function previewHeader(input) {
    const preview = document.getElementById('headerPreview');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            document.getElementById('headerPreviewContainer').classList.add('border-purple-500');

            // Сохраняем файл заголовка для последующей загрузки
            projectHeader = input.files[0];
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Предварительный просмотр изображений проекта
function previewProjectImages(input) {
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
                projectImages.push({
                    file: file,
                    preview: e.target.result
                });
            };

            reader.readAsDataURL(file);
        }
    }
}

// Удаление предпросмотра изображения
function removeImagePreview(button) {
    const previewElement = button.closest('.relative');
    const index = Array.from(previewElement.parentNode.children).indexOf(previewElement);

    if (index !== -1) {
        projectImages.splice(index, 1);
        previewElement.remove();
    }
}

// Удаление существующего изображения
function removeExistingImage(button, imageUrl) {
    const previewElement = button.closest('.relative');
    const index = Array.from(previewElement.parentNode.children).indexOf(previewElement);

    if (index !== -1) {
        projectImages.splice(index, 1);
        previewElement.remove();
    }
}

// Редактирование проекта
function editProject(projectId) {
    // Устанавливаем идентификатор текущего проекта
    currentProjectId = projectId;
    document.getElementById('projectId').value = projectId;
    document.getElementById('projectModalTitle').textContent = 'Edit Project';

    // Сбрасываем массивы и файлы
    projectImages = [];
    projectCollaborators = [];
    projectTags = [];
    projectThumbnail = null;
    projectHeader = null;

    // Получаем данные проекта
    fetch(`/projects/${projectId}`)
        .then(response => response.json())
        .then(project => {
            // Заполняем поля формы
            document.getElementById('projectTitle').value = project.title || '';
            document.getElementById('projectDescription').value = project.description || '';
            document.getElementById('projectGithub').value = project.github_url || '';
            document.getElementById('projectUrl').value = project.project_url || '';
            if (project.collaborators && project.collaborators.length > 0) {
                projectCollaborators = project.collaborators.map(collab => ({
                    username: collab.username,
                    full_name: collab.full_name,
                    avatar: collab.avatar,
                    user_id: collab.user_id,
                    status: collab.status || 'accepted'  // Default to 'accepted' for backward compatibility
                }));
                updateCollaboratorsUI();
            }
            // Загружаем миниатюру, если она существует
            if (project.thumbnail) {
                document.getElementById('thumbnailPreview').src = project.thumbnail;
                document.getElementById('thumbnailPreviewContainer').classList.add('border-purple-500');
            } else {
                document.getElementById('thumbnailPreview').src = '/static/placeholder.png';
                document.getElementById('thumbnailPreviewContainer').classList.remove('border-purple-500');
            }

            // Загружаем заголовок, если он существует
            if (project.header_image) {
                document.getElementById('headerPreview').src = project.header_image;
                document.getElementById('headerPreviewContainer').classList.add('border-purple-500');
            } else {
                document.getElementById('headerPreview').src = '/static/placeholder-wide.png';
                document.getElementById('headerPreviewContainer').classList.remove('border-purple-500');
            }

            // Загружаем теги
            if (project.tags && project.tags.length > 0) {
                projectTags = [...project.tags];
                updateTagsUI();
            }

            // Загружаем изображения
            if (project.images && project.images.length > 0) {
                const imagesContainer = document.getElementById('imagesContainer');
                imagesContainer.innerHTML = '';

                project.images.forEach(imageUrl => {
                    const imagePreview = document.createElement('div');
                    imagePreview.className = 'relative group';
                    imagePreview.innerHTML = `
                        <img src="${imageUrl}" alt="Project Image" 
                            class="w-full h-32 object-cover rounded-lg">
                        <div class="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <button type="button" class="p-1 bg-red-500 text-white rounded-full hover:bg-red-600 transition-colors"
                                onclick="removeExistingImage(this, '${imageUrl}')">
                                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    `;

                    imagesContainer.appendChild(imagePreview);

                    // Сохраняем существующий URL изображения
                    projectImages.push({
                        url: imageUrl,
                        isExisting: true
                    });
                });
            }

            // Загружаем сотрудников
            if (project.collaborators && project.collaborators.length > 0) {
                projectCollaborators = [...project.collaborators];
                updateCollaboratorsUI();
            }

            // Показываем модальное окно
            document.getElementById('projectModal').classList.add('modal-open');
        })
        .catch(error => {
            console.error('Project loading error:', error);
            showNotification('Error loading project information', 'error');
        });
}

// Удаление проекта
function deleteProject(projectId) {
    document.getElementById('projectToDelete').value = projectId;
    document.getElementById('deleteProjectModal').classList.add('modal-open');
}

// Закрытие модального окна подтверждения удаления
function closeDeleteProjectModal() {
    document.getElementById('deleteProjectModal').classList.remove('modal-open');
}

// ===== Функции для управления тегами =====

// Добавление тега к проекту
function addTag() {
    const tagInput = document.getElementById('tagInput');
    const tag = tagInput.value.trim();

    if (tag && !projectTags.includes(tag)) {
        projectTags.push(tag);
        updateTagsUI();
    }

    tagInput.value = '';
    tagInput.focus();
}

// Обновление интерфейса тегов
function updateTagsUI() {
    const tagsContainer = document.getElementById('tagsContainer');
    tagsContainer.innerHTML = '';

    projectTags.forEach((tag, index) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'px-3 py-1 bg-gray-200 text-gray-800 rounded-full flex items-center text-sm';
        tagElement.innerHTML = `
            <span>${tag}</span>
            <button type="button" class="ml-2 text-gray-500 hover:text-red-500"
                onclick="removeTag(${index})">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;

        tagsContainer.appendChild(tagElement);
    });
}

// Удаление тега
function removeTag(index) {
    projectTags.splice(index, 1);
    updateTagsUI();
}

// ===== Функции для управления сотрудниками проекта =====

// Поиск пользователей для добавления в качестве сотрудников
function searchUsers() {
    const input = document.getElementById('collaboratorInput');
    const query = input.value.trim();
    const resultsContainer = document.getElementById('userSearchResults');

    if (!query) {
        resultsContainer.classList.add('hidden');
        return;
    }

    // Показываем состояние загрузки
    resultsContainer.innerHTML = `
        <div class="p-3 text-sm text-gray-500 flex items-center justify-center">
            <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Поиск...
        </div>
    `;
    resultsContainer.classList.remove('hidden');

    fetch(`/search_users?query=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(users => {
            resultsContainer.innerHTML = '';

            if (users.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="p-3 text-sm text-gray-500">Пользователи не найдены</div>
                `;
            } else {
                users.forEach(user => {
                    // Убедимся, что у каждого пользователя есть свойство user_id
                    const userId = user.user_id || user.id;

                    // Пропускаем пользователей, которые уже являются сотрудниками
                    if (projectCollaborators.some(c => c.username === user.username)) {
                        return;
                    }

                    const userElement = document.createElement('div');
                    userElement.className = 'p-3 hover:bg-gray-50 flex items-center cursor-pointer';
                    userElement.innerHTML = `
                        <img src="${user.avatar}" alt="${user.username}" class="h-8 w-8 rounded-full mr-3">
                        <div>
                            <div class="text-sm font-medium">${user.full_name || user.username}</div>
                            <div class="text-xs text-gray-500">@${user.username}</div>
                        </div>
                    `;

                    userElement.addEventListener('click', () => {
                        addCollaborator({
                            username: user.username,
                            full_name: user.full_name || '',
                            avatar: user.avatar,
                            user_id: userId
                        });
                        resultsContainer.classList.add('hidden');
                        input.value = '';
                    });

                    resultsContainer.appendChild(userElement);
                });
            }

            resultsContainer.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Ошибка поиска пользователей:', error);
            resultsContainer.innerHTML = `
                <div class="p-3 text-sm text-red-500">Ошибка поиска пользователей</div>
            `;
        });
}



// Обновление интерфейса сотрудников
function updateCollaboratorsUI() {
    const container = document.getElementById('collaboratorsContainer');
    container.innerHTML = '';

    if (projectCollaborators.length === 0) {
        container.innerHTML = `
            <div class="text-sm text-gray-500 py-3">No collaborators added yet</div>
        `;
        return;
    }

    // Create list of collaborators with status indicators
    projectCollaborators.forEach((collaborator, index) => {
        const element = document.createElement('div');
        element.className = 'flex items-center justify-between bg-gray-50 p-3 rounded-lg mb-2 transform transition-all duration-300';
        element.style.opacity = '0';
        element.style.transform = 'translateY(10px)';

        // Create status indicator based on collaborator status
        const statusIndicator = collaborator.status === 'pending' ?
            `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                <svg class="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Pending
            </span>` :
            `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                <svg class="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Joined
            </span>`;

        element.innerHTML = `
            <div class="flex items-center">
                <img src="${collaborator.avatar}" alt="${collaborator.username}" class="h-8 w-8 rounded-full mr-3">
                <div>
                    <div class="text-sm font-medium">${collaborator.full_name || collaborator.username}</div>
                    <div class="flex items-center space-x-2">
                        <div class="text-xs text-gray-500">@${collaborator.username}</div>
                        ${statusIndicator}
                    </div>
                </div>
            </div>
            <button type="button" class="text-gray-500 hover:text-red-500 transition-colors p-2 rounded-full hover:bg-gray-100"
                onclick="removeCollaborator(${index})">
                <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;

        container.appendChild(element);

        // Animation
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Count badge with pending vs. accepted stats
    const pendingCount = projectCollaborators.filter(c => c.status === 'pending').length;
    const acceptedCount = projectCollaborators.length - pendingCount;

    const countBadge = document.createElement('div');
    countBadge.className = 'text-xs text-gray-500 text-right mt-2';

    if (pendingCount > 0) {
        countBadge.innerHTML = `
            ${projectCollaborators.length} collaborator${projectCollaborators.length !== 1 ? 's' : ''} 
            <span class="text-yellow-600">(${pendingCount} pending)</span>
        `;
    } else {
        countBadge.textContent = `${projectCollaborators.length} collaborator${projectCollaborators.length !== 1 ? 's' : ''}`;
    }

    container.appendChild(countBadge);
}



// ===== Настройка формы проекта =====

// Настройка формы проекта
function setupProjectForm() {
    const projectForm = document.getElementById('projectForm');
    if (projectForm) {
        projectForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span class="ml-2">Сохранение...</span>`;

            try {
                // Создаем объект FormData
                const formData = new FormData();
                formData.append('title', document.getElementById('projectTitle').value);
                formData.append('description', document.getElementById('projectDescription').value);
                formData.append('github_url', document.getElementById('projectGithub').value);
                formData.append('project_url', document.getElementById('projectUrl').value);

                // Добавляем миниатюру и заголовок, если они существуют
                if (projectThumbnail) {
                    formData.append('thumbnail', projectThumbnail);
                }

                if (projectHeader) {
                    formData.append('header_image', projectHeader);
                }

                // Убедимся, что массивы тегов и сотрудников преобразованы в строку
                formData.append('tags', JSON.stringify(projectTags));
                formData.append('collaborators', JSON.stringify(projectCollaborators));

                // Добавляем идентификатор проекта, если редактируем
                if (currentProjectId) {
                    formData.append('project_id', currentProjectId);
                }

                // Добавляем новые изображения
                let imageIndex = 0;
                projectImages.forEach(image => {
                    if (image.file) {
                        // Новый файл для загрузки
                        formData.append(`image_${imageIndex}`, image.file);
                        imageIndex++;
                    } else if (image.url && image.isExisting) {
                        // Существующее изображение для сохранения
                        formData.append('existing_images', image.url);
                    }
                });

                // Загружаем проект
                const url = currentProjectId ?
                    `/projects/${currentProjectId}/update` :
                    '/projects/create';

                const response = await fetch(url, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showNotification(
                        currentProjectId ?
                            'The project has been updated successfully' :
                            'The project has been successfully created'
                    );
                    closeProjectModal();

                    // Перезагружаем страницу для отображения нового/обновленного проекта
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(result.error || 'Не удалось сохранить проект');
                }
            } catch (error) {
                console.error('Error saving project:', error);
                showNotification('Error saving project. Please try again.', 'error');
            } finally {
                // Включаем кнопку снова
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Project';
            }
        });
    }
}

// Настройка кнопки подтверждения удаления
function setupDeleteConfirmation() {
    const confirmDeleteBtn = document.getElementById('confirmDeleteProjectBtn');
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', async function () {
            const projectId = document.getElementById('projectToDelete').value;

            if (!projectId) return;

            this.disabled = true;
            this.innerHTML = `<svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span class="ml-2">Удаление...</span>`;

            try {
                const response = await fetch(`/projects/${projectId}/delete`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.success) {
                    showNotification('The project has been successfully deleted.');
                    closeDeleteProjectModal();

                    // Перезагружаем страницу
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    throw new Error(result.error || 'Failed to delete project');
                }
            } catch (error) {
                console.error('Error deleting project:', error);
                showNotification('Error deleting project. Please try again.', 'error');
            } finally {
                this.disabled = false;
                this.innerHTML = 'Delete';
            }
        });
    }
    function renderCollaborator(collaborator) {
        return `
        <div class="collaborator-item flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full overflow-hidden">
                    <img src="${collaborator.avatar || 'https://ui-avatars.com/api/?name=' + encodeURIComponent(collaborator.username[0]) + '&background=random&color=fff&size=128'}" 
                         alt="${collaborator.username}" 
                         class="collaborator-avatar w-full h-full object-cover">
                </div>
                <div>
                    <h4 class="font-medium">${collaborator.username}</h4>
                    <p class="text-sm text-gray-500">${collaborator.full_name || ''}</p>
                </div>
            </div>
            <button type="button" onclick="removeCollaborator('${collaborator.user_id}')" 
                    class="text-red-500 hover:bg-red-50 p-2 rounded-full transition-colors">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
        `;
    }
    // Обработчик клика вне результатов поиска
    document.addEventListener('click', function (e) {
        const searchResults = document.getElementById('userSearchResults');
        const searchInput = document.getElementById('collaboratorInput');

        if (searchResults && !searchResults.contains(e.target) && e.target !== searchInput) {
            searchResults.classList.add('hidden');
        }
    });
}
// Update collaborator display UI


// Add collaborator with pending status
function addCollaborator(user) {
    // Check if user is not already a collaborator
    if (!projectCollaborators.some(c => c.username === user.username)) {
        projectCollaborators.push({
            username: user.username,
            full_name: user.full_name,
            avatar: user.avatar,
            user_id: user.user_id,
            status: 'pending'  // Default status for new collaborators
        });

        updateCollaboratorsUI();
        showNotification(`Added @${user.username} as a pending collaborator`, 'success');
    } else {
        showNotification(`@${user.username} is already added`, 'info');
    }
}

// Confirmation dialog with different message based on status
function removeCollaborator(index) {
    const collaborator = projectCollaborators[index];
    const isPending = collaborator.status === 'pending';

    const message = isPending ?
        `Cancel invitation to ${collaborator.full_name || collaborator.username}?` :
        `Remove ${collaborator.full_name || collaborator.username} from collaborators?`;

    if (confirm(message)) {
        projectCollaborators.splice(index, 1);
        updateCollaboratorsUI();

        const notification = isPending ?
            `Cancelled invitation to @${collaborator.username}` :
            `Removed @${collaborator.username} from collaborators`;

        showNotification(notification, 'success');
    }
}

