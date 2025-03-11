/**
 * skills.js - Управление навыками
 * 
 * Этот файл содержит функции для управления навыками пользователя:
 * - Добавление, удаление и редактирование навыков
 * - Сохранение навыков
 * - Отображение навыков
 */

// ===== Глобальные переменные =====

// Текущие навыки пользователя
let currentSkills = [];

// ===== Обработчики событий навыков =====

document.addEventListener('DOMContentLoaded', function () {
    console.log('Skills JavaScript загружен');

    // Инициализация массива навыков из DOM
    initializeSkills();

    // Настройка редактора навыков
    setupSkillsEditor();
});

// ===== Функции для управления навыками =====

// Инициализация массива навыков из DOM
function initializeSkills() {
    const skillsContainer = document.getElementById('skillsContainer');
    if (skillsContainer) {
        // Получаем навыки из интерфейса
        window.currentSkills = Array.from(skillsContainer.querySelectorAll('span'))
            .map(span => span.textContent.trim());
    }

    console.log("Инициализированы навыки:", window.currentSkills);
}

// Настройка редактора навыков
function setupSkillsEditor() {
    // Добавляем глобальные функции для взаимодействия с HTML
    window.showSkillsEditor = showSkillsEditor;
    window.closeSkillsModal = closeSkillsModal;
    window.addNewSkill = addNewSkill;
    window.saveSkills = saveSkills;

    // Настройка кнопки редактирования навыков
    const skillsEditorBtn = document.querySelector('button[onclick="showSkillsEditor()"]');
    if (skillsEditorBtn) {
        skillsEditorBtn.removeAttribute('onclick');
        skillsEditorBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            showSkillsEditor();
        });
    }

    // Предотвращение закрытия модального окна при клике внутри
    const skillsModal = document.getElementById('skillsModal');
    if (skillsModal) {
        const modalBox = skillsModal.querySelector('.modal-box');
        if (modalBox) {
            modalBox.addEventListener('click', function (e) {
                e.stopPropagation();
            });
        }
    }
}

// Отображение редактора навыков
function showSkillsEditor(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    console.log('Showing skills editor');
    const modal = document.getElementById('skillsModal');
    const skillsList = document.getElementById('skillsList');

    if (!modal || !skillsList) {
        console.error('Skills modal or skills list not found', { modal, skillsList });
        return;
    }

    // Ensure we have the current skills
    if (!window.currentSkills) {
        window.currentSkills = [];
        const skillsContainer = document.getElementById('skillsContainer');
        if (skillsContainer) {
            window.currentSkills = Array.from(skillsContainer.querySelectorAll('span'))
                .map(span => span.textContent.trim());
        }
    }

    console.log('Current skills:', window.currentSkills);

    // Clear and repopulate the skills list
    skillsList.innerHTML = '';
    window.currentSkills.forEach(skill => {
        console.log('Adding skill input for:', skill);
        addSkillInput(skill);
    });

    // Make sure modal is visible
    modal.classList.add('modal-open');
}


// Закрытие модального окна навыков
function closeSkillsModal(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    const modal = document.getElementById('skillsModal');
    if (modal) {
        modal.classList.remove('modal-open');
    }
}

// Добавление поля ввода для навыка
function addSkillInput(value = '') {
    const skillsList = document.getElementById('skillsList');
    if (!skillsList) {
        console.error('Skills list not found');
        return;
    }

    const skillDiv = document.createElement('div');
    skillDiv.className = 'flex items-center gap-2 mb-2';
    skillDiv.innerHTML = `
        <input type="text" class="input input-bordered flex-1" 
            placeholder="Enter skill (e.g., Python, C++)" 
            maxlength="20" value="${value || ''}">
        <button type="button" class="btn btn-ghost btn-sm text-red-500 hover:bg-red-50">
            Remove
        </button>
    `;

    // Add click handler for the remove button
    const removeBtn = skillDiv.querySelector('button');
    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            skillDiv.remove();
        });
    }

    skillsList.appendChild(skillDiv);
}

// Добавление нового навыка
function addNewSkill(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }
    addSkillInput();
}

// Сохранение навыков
async function saveSkills(e) {
    if (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    const inputs = document.querySelectorAll('#skillsList input');
    const skills = Array.from(inputs)
        .map(input => input.value.trim())
        .filter(skill => skill !== '');

    console.log('Saving skills:', skills);

    try {
        const response = await fetch('/update-skills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ skills })
        });

        const data = await response.json();
        if (data.success) {
            // Update the global array
            window.currentSkills = skills;
            console.log('Updated currentSkills:', window.currentSkills);

            // Update the UI
            updateSkillsDisplay();
            updateProfileSkillsDisplay();

            closeSkillsModal();
            showNotification('Skills updated successfully');
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error updating skills:', error);
        showNotification('Failed to update skills', 'error');
    }
}
// Function to update skills display in the UI
function updateSkillsDisplay() {
    console.log('Updating skills display with:', window.currentSkills);

    // 1. Update the skills container in the edit form
    const skillsContainer = document.getElementById('skillsContainer');
    if (skillsContainer) {
        skillsContainer.innerHTML = '';

        if (window.currentSkills && window.currentSkills.length > 0) {
            window.currentSkills.forEach(skill => {
                const skillSpan = document.createElement('span');
                skillSpan.className = 'px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full hover:bg-purple-100 transition-colors';
                skillSpan.textContent = skill;
                skillsContainer.appendChild(skillSpan);
            });
        } else {
            skillsContainer.innerHTML = '<span class="text-gray-400">No skills added yet</span>';
        }
    }

    // 2. Update skills in the profile display section
    const profileDisplayInfo = document.getElementById('profileDisplayInfo');
    if (profileDisplayInfo) {
        // Find existing skills section if any
        let skillsSection = null;
        const sections = profileDisplayInfo.querySelectorAll('div > div');

        for (const section of sections) {
            const heading = section.querySelector('h3');
            if (heading && heading.textContent.trim() === 'Skills') {
                skillsSection = section;
                break;
            }
        }

        // If skills exist, either update existing section or create new one
        if (window.currentSkills && window.currentSkills.length > 0) {
            const skillsHTML = `
                <h3 class="font-medium text-gray-700">Skills</h3>
                <div class="flex flex-wrap gap-2 mt-2">
                    ${window.currentSkills.map(skill => `
                        <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                            ${skill}
                        </span>
                    `).join('')}
                </div>
            `;

            if (skillsSection) {
                // Update existing section
                skillsSection.innerHTML = skillsHTML;
            } else {
                // Create new section
                const container = profileDisplayInfo.querySelector('.space-y-4');
                if (container) {
                    const newSection = document.createElement('div');
                    newSection.innerHTML = skillsHTML;
                    container.appendChild(newSection);
                }
            }
        } else if (skillsSection) {
            // If no skills but section exists, remove it
            skillsSection.remove();
        }
    }

    console.log('Skills display updated');
}

// Обновление отображения навыков
function updateProfileSkillsDisplay() {
    console.log('Updating profile skills display');
    const displayInfo = document.getElementById('profileDisplayInfo');
    if (!displayInfo) return;

    // Look for existing skills section
    let skillsSection = null;
    const allSections = displayInfo.querySelectorAll('div > div');

    for (const section of allSections) {
        const heading = section.querySelector('h3');
        if (heading && heading.textContent.trim() === 'Skills') {
            skillsSection = section;
            break;
        }
    }

    // If skills section exists, update it
    if (skillsSection) {
        if (window.currentSkills && window.currentSkills.length > 0) {
            // Update existing section
            skillsSection.innerHTML = `
                <h3 class="font-medium text-gray-700">Skills</h3>
                <div class="flex flex-wrap gap-2 mt-2">
                    ${window.currentSkills.map(skill => `
                        <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                            ${skill}
                        </span>
                    `).join('')}
                </div>
            `;
        } else {
            // Remove skills section if empty
            skillsSection.remove();
        }
    } else if (window.currentSkills && window.currentSkills.length > 0) {
        // Create new skills section if it doesn't exist
        const container = displayInfo.querySelector('.space-y-4');
        if (container) {
            const newSection = document.createElement('div');
            newSection.innerHTML = `
                <h3 class="font-medium text-gray-700">Skills</h3>
                <div class="flex flex-wrap gap-2 mt-2">
                    ${window.currentSkills.map(skill => `
                        <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                            ${skill}
                        </span>
                    `).join('')}
                </div>
            `;
            container.appendChild(newSection);
        }
    }
}
function updateAllSkillsDisplays() {
    // 1. Update the main skills container in the profile info section
    const mainSkillsContainer = document.getElementById('skillsContainer');
    if (mainSkillsContainer) {
        mainSkillsContainer.innerHTML = window.currentSkills.map(skill => `
            <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full hover:bg-purple-100 transition-colors">
                ${skill}
            </span>
        `).join('');
    }

    // 2. Update skills in the profile display section
    const profileDisplayInfo = document.getElementById('profileDisplayInfo');
    if (profileDisplayInfo) {
        const skillsSection = profileDisplayInfo.querySelector('div:has(h3:contains("Skills"))');

        if (skillsSection) {
            // If skills section exists, update it
            skillsSection.innerHTML = `
            <h3 class="font-medium text-gray-700">Skills</h3>
            <div class="flex flex-wrap gap-2 mt-2">
                ${window.currentSkills.map(skill => `
                <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                    ${skill}
                </span>
                `).join('')}
            </div>`;
        } else if (window.currentSkills.length > 0) {
            // If skills section doesn't exist but we have skills, add it
            const newSkillsSection = document.createElement('div');
            newSkillsSection.innerHTML = `
            <h3 class="font-medium text-gray-700">Skills</h3>
            <div class="flex flex-wrap gap-2 mt-2">
                ${window.currentSkills.map(skill => `
                <span class="px-3 py-1 text-sm font-medium bg-purple-50 text-purple-700 rounded-full">
                    ${skill}
                </span>
                `).join('')}
            </div>`;
            profileDisplayInfo.querySelector('.space-y-4').appendChild(newSkillsSection);
        }
    }
}