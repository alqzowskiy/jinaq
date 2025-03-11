/**
 * core.js - Основные утилиты и общие функции
 * 
 * Этот файл содержит базовые функции, используемые во всем приложении:
 * - Уведомления
 * - Утилиты для работы с DOM
 * - Обработчики событий
 * - Функции для отображения/скрытия модальных окон
 */

// ===== Глобальные утилиты =====

// Функция для отображения уведомлений
function showNotification(message, type = 'success') {
    // Удаляем существующие уведомления
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());

    // Создаем элемент уведомления
    const toast = document.createElement('div');
    toast.className = `toast-notification fixed bottom-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg 
                 ${type === 'error' ? 'bg-red-500' : 'bg-black'} text-white
                 opacity-0 transform translate-y-4 transition-all duration-300`;
    toast.textContent = message;

    // Добавляем в DOM
    document.body.appendChild(toast);

    // Запускаем анимацию появления
    setTimeout(() => {
        toast.classList.remove('opacity-0');
        toast.classList.remove('translate-y-4');
    }, 10);

    // Автоматически удаляем через 3 секунды
    setTimeout(() => {
        toast.classList.add('opacity-0');
        toast.classList.add('translate-y-4');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Утилиты для работы с DOM
const utils = {
    // Функция debounce для ограничения частоты вызова функций
    debounce: function (func, delay) {
        let timeoutId;
        return (...args) => {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => func.apply(null, args), delay);
        };
    },

    // Создание HTML элементов
    createElement: function (tagName, className, innerHTML = '') {
        const element = document.createElement(tagName);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    }
};

// ===== Обработчики модальных окон =====

// Функция для открытия модального окна
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('modal-open');
    }
}

// Функция для закрытия модального окна
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('modal-open');
    }
}

// Функция для копирования ссылки на профиль
// Add this to your profile.js file or directly in a <script> tag at the end of profile.html

// Ensure copyProfileLink is properly defined and accessible
function copyProfileLink() {
    // Check for the meta tag first
    const usernameMeta = document.querySelector('meta[name="current-username"]');
    let username;

    if (usernameMeta && usernameMeta.content) {
        username = usernameMeta.content;
    } else {
        // Fallback: Try to extract username from the page content
        // Look for the username display in the profile content
        const usernameElement = document.querySelector('p.text-gray-600 > span') ||
            document.querySelector('p.text-gray-600');

        if (usernameElement) {
            // Extract text that starts with @ symbol
            const text = usernameElement.textContent.trim();
            const matches = text.match(/@([a-zA-Z0-9_]+)/);
            if (matches && matches[1]) {
                username = matches[1];
            }
        }

        // If still no username, try to get it from URL
        if (!username) {
            const pathParts = window.location.pathname.split('/');
            // Assume the last part of the URL path is the username if on profile page
            if (pathParts.length > 1 && pathParts[1]) {
                username = pathParts[1];
            }
        }
    }

    if (!username) {
        showNotification('Username not found. Please reload the page and try again.', 'error');
        return;
    }

    const profileLink = window.location.origin + '/' + username;

    // Use modern clipboard API with fallback
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(profileLink)
            .then(() => {
                showNotification('Profile link copied to clipboard!');
            })
            .catch(err => {
                console.error('Failed to copy: ', err);
                showNotification('Failed to copy link', 'error');
                fallbackCopyTextToClipboard(profileLink);
            });
    } else {
        fallbackCopyTextToClipboard(profileLink);
    }
}

// Fallback for browsers that don't support clipboard API
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;

    // Make the textarea out of viewport
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showNotification('Profile link copied to clipboard!');
        } else {
            showNotification('Failed to copy link', 'error');
        }
    } catch (err) {
        console.error('Fallback: Oops, unable to copy', err);
        showNotification('Failed to copy link', 'error');
    }

    document.body.removeChild(textArea);
}

// Make sure the showNotification function is available
if (typeof showNotification !== 'function') {
    function showNotification(message, type = 'success') {
        // Remove existing notifications
        const existingToasts = document.querySelectorAll('.toast-notification');
        existingToasts.forEach(toast => toast.remove());

        // Create notification element
        const toast = document.createElement('div');
        toast.className = `toast-notification fixed bottom-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg 
                     ${type === 'error' ? 'bg-red-500' : 'bg-black'} text-white
                     opacity-0 transform translate-y-4 transition-all duration-300`;
        toast.textContent = message;

        // Add to DOM
        document.body.appendChild(toast);

        // Trigger animation
        setTimeout(() => {
            toast.classList.remove('opacity-0');
            toast.classList.remove('translate-y-4');
        }, 10);

        // Automatically remove after 3 seconds
        setTimeout(() => {
            toast.classList.add('opacity-0');
            toast.classList.add('translate-y-4');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Ensure that all click handlers are properly attached after DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    // Attach click handler to all elements with the functionality
    const copyBtns = document.querySelectorAll('button[onclick="copyProfileLink()"]');
    copyBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            copyProfileLink();
        });
    });

    console.log('Copy profile link handlers attached');
});
function setupModalSystem() {
    // Generic open modal function
    window.openModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            window.debug('Opening modal', modalId);
            modal.classList.add('modal-open');

            // Set active modal in data attribute
            document.body.setAttribute('data-active-modal', modalId);
        }
    };

    // Generic close modal function
    window.closeModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            window.debug('Closing modal', modalId);
            modal.classList.remove('modal-open');

            // Clear active modal
            document.body.removeAttribute('data-active-modal');
        }
    };

    // ESC key to close modals
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            const activeModalId = document.body.getAttribute('data-active-modal');
            if (activeModalId) {
                window.closeModal(activeModalId);
            }
        }
    });
}
// ===== Инициализация при загрузке страницы =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('Core JavaScript загружен');
    checkProfileNavigation();
    // Настройка флага редактирования
    setupEditModePersistence();

    // Добавляем обработчики для модальных окон
    setupModalHandlers();
});

function storageAvailable(type) {
    let storage;
    try {
        storage = window[type];
        const x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    } catch (e) {
        return false;
    }
}
function setupEditModePersistence() {
    // Hide the loading overlay and show content when everything is ready
    function showProfileContent() {
        const loadingOverlay = document.getElementById('profileLoadingOverlay');
        if (loadingOverlay) {
            // Fade out the loading overlay
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }

        // Mark the body as ready to show content
        document.body.classList.add('profile-content-ready');

        // Also make the profile content visible
        const profileContent = document.getElementById('profileContent');
        if (profileContent) {
            profileContent.style.opacity = '1';
        }
    }

    const editBtn = document.getElementById('editProfileBtn');
    if (!editBtn) {
        // If there's no edit button, we're not on the profile page
        showProfileContent(); // Show content anyway
        return;
    }

    // Check if we're on the profile page
    const isProfilePage = window.location.pathname === '/profile';

    if (isProfilePage) {
        // If we're on the profile page, record the timestamp
        localStorage.setItem('profileLastVisited', Date.now());
    } else {
        // If we're not on the profile page, clear edit mode
        localStorage.removeItem('profileEditMode');
        localStorage.removeItem('profileLastVisited');
        showProfileContent(); // Show content since we're not on profile page
        return;
    }

    // Check for stale edit mode state
    const lastVisited = localStorage.getItem('profileLastVisited');
    if (lastVisited) {
        const timeSinceLastVisit = Date.now() - parseInt(lastVisited);
        // If it's been more than 30 seconds and we're not on the profile page, clear edit mode
        if (timeSinceLastVisit > 30000 && !isProfilePage) {
            localStorage.removeItem('profileEditMode');
            localStorage.removeItem('profileLastVisited');
        }
    }

    // Check if we should be in edit mode
    const shouldBeInEditMode = isProfilePage && localStorage.getItem('profileEditMode') === 'true';

    // Elements to show/hide
    const editableSections = document.querySelectorAll('.profile-editable-section');
    const displaySections = document.querySelectorAll('.profile-display-section');
    const headerContainer = document.getElementById('headerContainer');
    const floatingSaveBtn = document.getElementById('floatingSaveBtn');

    // Initialize edit mode based on saved state, but do it correctly to avoid flashing
    if (shouldBeInEditMode) {
        // Apply edit mode styles directly before removing !important via classes
        editableSections.forEach(section => {
            section.style.display = 'block';
        });
        displaySections.forEach(section => {
            section.style.display = 'none';
        });
        if (headerContainer) headerContainer.style.display = 'block';
        if (floatingSaveBtn) floatingSaveBtn.style.display = 'flex';

        // Update button 
        editBtn.textContent = 'Cancel Editing';
        editBtn.classList.add('bg-gray-600');
        editBtn.classList.remove('bg-black');
    } else {
        // Apply display mode styles directly
        editableSections.forEach(section => {
            section.style.display = 'none';
        });
        displaySections.forEach(section => {
            section.style.display = 'block';
        });
        if (headerContainer) headerContainer.style.display = 'none';
        if (floatingSaveBtn) floatingSaveBtn.style.display = 'none';

        // Update button
        editBtn.textContent = 'Edit Profile';
        editBtn.classList.remove('bg-gray-600');
        editBtn.classList.add('bg-black');
    }

    // Now we can remove the !important CSS classes since we've directly set the styles
    editableSections.forEach(section => {
        section.classList.remove('profile-editable-section');
        section.classList.add('profile-editable');
    });

    displaySections.forEach(section => {
        section.classList.remove('profile-display-section');
        section.classList.add('profile-display');
    });

    // Show the content now that we've set up the correct state
    setTimeout(showProfileContent, 100);

    // Update event listener for toggling edit mode
    editBtn.addEventListener('click', function () {
        const isCurrentlyInEditMode = this.textContent.includes('Cancel');

        if (!isCurrentlyInEditMode) {
            // Enter edit mode
            enterEditMode();
            localStorage.setItem('profileEditMode', 'true');
            localStorage.setItem('profileLastVisited', Date.now());
        } else {
            // Exit edit mode
            exitEditMode();
            localStorage.setItem('profileEditMode', 'false');
        }
    });

    // Update last visited timestamp periodically when on profile page
    if (isProfilePage) {
        setInterval(function () {
            localStorage.setItem('profileLastVisited', Date.now());
        }, 5000); // Update every 5 seconds
    }

    // Function to enter edit mode
    function enterEditMode() {
        // Show editable sections
        document.querySelectorAll('.profile-editable').forEach(section => {
            section.style.display = 'block';
        });

        // Hide display sections
        document.querySelectorAll('.profile-display').forEach(section => {
            section.style.display = 'none';
        });

        // Show header container and floating save button
        if (headerContainer) {
            headerContainer.style.display = 'block';
        }
        if (floatingSaveBtn) {
            floatingSaveBtn.style.display = 'flex';
        }
        document.querySelectorAll('.cert-checkbox').forEach(checkbox => {
            checkbox.style.display = 'block';
        });


        editBtn.textContent = 'Cancel Editing';
        editBtn.classList.add('bg-gray-600');
        editBtn.classList.remove('bg-black');
    }

    // Function to exit edit mode
    function exitEditMode() {
        // Hide editable sections
        document.querySelectorAll('.profile-editable').forEach(section => {
            section.style.display = 'none';
        });

        // Show display sections
        document.querySelectorAll('.profile-display').forEach(section => {
            section.style.display = 'block';
        });

        // Hide header container and floating save button
        if (headerContainer) {
            headerContainer.style.display = 'none';
        }
        if (floatingSaveBtn) {
            floatingSaveBtn.style.display = 'none';
        }
        // Hide certificate checkboxes
        document.querySelectorAll('.cert-checkbox').forEach(checkbox => {
            checkbox.style.display = 'none';
            checkbox.checked = false; // Uncheck all checkboxes
        });



        // Clear selected certificates
        selectedCertificates = [];
        // Update button text and style
        editBtn.textContent = 'Edit Profile';
        editBtn.classList.remove('bg-gray-600');
        editBtn.classList.add('bg-black');
    }
}

// Настройка обработчиков для модальных окон
// Update in core.js
function setupModalHandlers() {
    console.log('Setting up modal handlers');

    // Close modals when clicking outside
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function (e) {
            if (e.target === this) {
                this.classList.remove('modal-open');
            }
        });
    });

    // Prevent clicks inside modal content from closing the modal
    document.querySelectorAll('.modal .modal-box').forEach(box => {
        box.addEventListener('click', function (e) {
            e.stopPropagation();
        });
    });
}
// Функция для инициализации обработчиков для кнопок с data атрибутами
function initDataAttributeHandlers() {
    // Обработчики для сертификатов
    document.querySelectorAll('.delete-certificate-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const certId = this.getAttribute('data-cert-id');
            if (certId) window.deleteCertificate(certId);
        });
    });

    // Обработчики для проектов
    document.querySelectorAll('.edit-project-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const projectId = this.getAttribute('data-project-id');
            if (projectId && typeof window.editProject === 'function') {
                window.editProject(projectId);
            }
        });
    });

    document.querySelectorAll('.delete-project-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            const projectId = this.getAttribute('data-project-id');
            if (projectId && typeof window.deleteProject === 'function') {
                window.deleteProject(projectId);
            }
        });
    });

    // Простые обработчики по ID
    const idHandlers = {
        'showUploadModalBtn': () => window.showUploadModal(),
        'closeUploadModalBtn': () => window.closeUploadModal(),
        'showCreateProjectModalBtn': () => window.showCreateProjectModal(),
        'closeProjectModalBtn': () => window.closeProjectModal(),
        'showSkillsEditorBtn': (e) => window.showSkillsEditor(e),
        'closeSkillsModalBtn': (e) => window.closeSkillsModal(e),
        'saveSkillsBtn': (e) => window.saveSkills(e),
        'addNewSkillBtn': (e) => window.addNewSkill(e)
    };

    Object.entries(idHandlers).forEach(([id, handler]) => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('click', handler);
        }
    });
}

// Добавляем вызов этой функции при загрузке документа
document.addEventListener('DOMContentLoaded', function () {

    initDataAttributeHandlers();
});
window.debug = function (message, data) {
    console.log(`[DEBUG] ${message}`, data || '');

    // Optional: show in UI for easier troubleshooting
    const debugOutput = document.getElementById('debugOutput');
    const debugContent = document.getElementById('debugContent');

    if (debugOutput && debugContent) {
        debugOutput.classList.remove('hidden');
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        const line = `[${timestamp}] ${message} ${data ? JSON.stringify(data) : ''}`;
        debugContent.textContent = line + '\n' + debugContent.textContent;
    }
};
function checkProfileNavigation() {
    // Get current path
    const currentPath = window.location.pathname;
    const isProfilePage = currentPath === '/profile';

    // If we're not on the profile page, clear the edit mode
    if (!isProfilePage) {
        localStorage.removeItem('profileEditMode');
        console.log('Not on profile page, cleared edit mode state');
    } else {
        console.log('On profile page, edit mode state preserved');
    }
}
