/**
 * Enhanced University Recommendations
 * 
 * This file contains improved recommendation functionality including:
 * - Better UI for university cards
 * - "Learn More" functionality for detailed university information
 * - Enhanced presentation of admission chances
 * - Improved user experience
 */

// Global variables for storing recommendation results
let currentRecommendationResults = null;
let expandedUniversityDetails = {};

// Show the university recommendations sidebar
function showUniversityRecommendations() {
    // Collect profile data and update sidebar
    const profileData = collectProfileData();
    updateRecommendationSidebar(profileData);

    // Open the sidebar
    const modal = document.getElementById('universityRecommendationsModal');
    if (modal) {
        modal.classList.remove('translate-x-full');
        document.body.classList.add('overflow-hidden');
    }
}

// Close the university recommendations sidebar
function closeUniversityRecommendations() {
    const modal = document.getElementById('universityRecommendationsModal');
    if (modal) {
        modal.classList.add('translate-x-full');
        document.body.classList.remove('overflow-hidden');
    }
}

// Function to collect profile data for recommendations
function collectProfileData() {
    // Get current skills
    const skills = window.currentSkills || [];

    return {
        academic: {
            gpa: document.querySelector('input[name="gpa"]')?.value || '',
            satScore: document.querySelector('input[name="sat_score"]')?.value || '',
            toeflScore: document.querySelector('input[name="toefl_score"]')?.value || '',
            ieltsScore: document.querySelector('input[name="ielts_score"]')?.value || ''
        },
        personal: {
            specialty: document.querySelector('input[name="specialty"]')?.value || '',
            goals: document.querySelector('textarea[name="goals"]')?.value || '',
            education: document.querySelector('textarea[name="education"]')?.value || '',
            bio: document.querySelector('textarea[name="bio"]')?.value || '',
            age: document.querySelector('input[name="age"]')?.value || '',
            skills: skills
        },
        languages: collectLanguages(),
        achievements: collectAchievements(),
        certificates: window.userCertificates || []
    };
}

// Collect language data from the form
function collectLanguages() {
    const languages = [];
    const languageInputs = document.querySelectorAll('#languagesContainer input[name="language_name"]');
    const levelInputs = document.querySelectorAll('#languagesContainer select[name="language_level"]');

    for (let i = 0; i < languageInputs.length; i++) {
        if (languageInputs[i].value.trim()) {
            languages.push({
                name: languageInputs[i].value.trim(),
                level: levelInputs[i].value
            });
        }
    }

    return languages;
}

// Collect achievement data from the form
function collectAchievements() {
    const achievements = [];
    const achievementContainers = document.querySelectorAll('#achievementsContainer > div');

    achievementContainers.forEach(container => {
        const title = container.querySelector('input[name="achievement_title"]')?.value || '';
        const description = container.querySelector('textarea[name="achievement_description"]')?.value || '';
        const date = container.querySelector('input[name="achievement_date"]')?.value || '';

        if (title.trim()) {
            achievements.push({
                title: title.trim(),
                description: description.trim(),
                date: date
            });
        }
    });

    return achievements;
}

// Update the sidebar with user profile data
function updateRecommendationSidebar(profileData) {
    try {
        // Update certificates list
        const certificatesList = document.getElementById('certificatesList');
        if (certificatesList) {
            const certificates = profileData.certificates || [];
            if (certificates && certificates.length > 0) {
                certificatesList.innerHTML = certificates.map(cert => `
                <div class="flex items-center gap-2 text-sm">
                    <svg class="w-4 h-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span class="truncate">${cert.title || 'Unnamed Certificate'}</span>
                </div>
            `).join('');
            } else {
                certificatesList.innerHTML = '<span class="text-gray-500 text-sm">No certificates uploaded</span>';
            }
        }

        // Add a backup for skills
        const skills = profileData.personal?.skills ||
            profileData.skills ||
            window.currentSkills || [];

        // Update skills display
        const skillsBadges = document.getElementById('skillsBadges');
        if (skillsBadges) {
            if (skills && skills.length > 0) {
                skillsBadges.innerHTML = skills.map(skill =>
                    `<span class="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-full">${skill}</span>`
                ).join('');
            } else {
                skillsBadges.innerHTML = '<span class="text-gray-500 text-sm">No skills added</span>';
            }
        }

        // Update academic metrics
        const profileGpa = document.getElementById('profileGpa');
        if (profileGpa) profileGpa.textContent = profileData.academic.gpa || 'Not provided';

        const profileToefl = document.getElementById('profileToefl');
        if (profileToefl) profileToefl.textContent = profileData.academic.toeflScore || 'Not provided';

        const profileIelts = document.getElementById('profileIelts');
        if (profileIelts) profileIelts.textContent = profileData.academic.ieltsScore || 'Not provided';

        const profileSat = document.getElementById('profileSat');
        if (profileSat) profileSat.textContent = profileData.academic.satScore || 'Not provided';

        // Update personal information
        const profileSpecialty = document.getElementById('profileSpecialty');
        if (profileSpecialty) profileSpecialty.textContent = profileData.personal.specialty || 'Not specified';

        const profileAge = document.getElementById('profileAge');
        if (profileAge) profileAge.textContent = profileData.personal.age ? `${profileData.personal.age} years old` : 'Not specified';

        const profileEducation = document.getElementById('profileEducation');
        if (profileEducation) profileEducation.textContent = profileData.personal.education || 'No education details provided';

        const profileGoals = document.getElementById('profileGoals');
        if (profileGoals) profileGoals.textContent = profileData.personal.goals || 'No goals specified';

        const profileBio = document.getElementById('profileBio');
        if (profileBio) profileBio.textContent = profileData.personal.bio || 'No bio provided';

        console.log('Sidebar updated successfully');
    } catch (error) {
        console.error('Error updating sidebar:', error);
    }
}

// Get university recommendations based on profile
function getRecommendations() {
    try {
        // Check if country is selected
        const countrySelect = document.getElementById('countrySelect');
        if (!countrySelect || !countrySelect.value) {
            showNotification('Please select a country', 'error');
            return;
        }

        // Get profile data and update sidebar
        const profileData = collectProfileData();
        updateRecommendationSidebar(profileData);

        // Show loading state
        const loadingState = document.getElementById('loadingState');
        const emptyState = document.getElementById('emptyState');
        const recommendationsContainer = document.getElementById('recommendationsContainer');

        if (loadingState) loadingState.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';
        if (recommendationsContainer) recommendationsContainer.style.display = 'none';

        // Send request to server
        fetch('/get-university-recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                country: countrySelect.value,
                profile: profileData.personal,
                academic: profileData.academic,
                languages: profileData.languages,
                achievements: profileData.achievements,
                certificates: profileData.certificates
            })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Recommendations received:', data);

                // Ensure admission chances are available
                data = ensureAdmissionChances(data);

                // Hide loading, show results
                if (loadingState) loadingState.style.display = 'none';
                if (recommendationsContainer) recommendationsContainer.style.display = 'block';

                // Display results
                renderRecommendations(data);
            })
            .catch(error => {
                console.error('Error fetching recommendations:', error);
                currentRecommendationResults = null; // Clear saved recommendations on error

                if (loadingState) loadingState.style.display = 'none';
                if (emptyState) {
                    emptyState.style.display = 'block';
                    emptyState.innerHTML = `
                    <div class="p-8 text-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto text-red-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h3 class="text-xl font-semibold mb-2">Error Getting Recommendations</h3>
                        <p class="text-gray-600 mb-4">${error.message || 'Unknown error occurred'}</p>
                        <button id="retryButton" class="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors">
                            Try Again
                        </button>
                    </div>
                `;

                    // Add retry button handler
                    document.getElementById('retryButton')?.addEventListener('click', getRecommendations);
                }
            });
    } catch (error) {
        console.error('Error in getRecommendations:', error);
        showNotification('An error occurred while getting recommendations', 'error');
    }
}

// Display university recommendations
function renderRecommendations(data) {
    console.log('Rendering recommendations:', data);

    // Save data for future tab switches
    currentRecommendationResults = data;

    const recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) return;

    // Clear existing list
    recommendationsList.innerHTML = '';

    // Get universities from response
    const universities = data.universities || [];

    if (universities.length === 0) {
        recommendationsList.innerHTML = `
            <div class="bg-white rounded-lg shadow-sm p-6 text-center">
                <h3 class="text-lg font-medium text-gray-700 mb-2">No Universities Found</h3>
                <p class="text-gray-500 mb-4">Try selecting a different country or updating your profile</p>
            </div>
        `;
        return;
    }

    // Check profile completeness and suggest filling missing data
    if (!checkProfileCompleteness()) {
        // checkProfileCompleteness will add the notice itself
    }

    // Create cards for each university
    universities.forEach((universityName, index) => {
        try {
            // Get university details
            const details = extractUniversityDetails(data.recommendations, universityName);
            const admissionChance = data.admission_chances?.[universityName] || 50;
            const imageUrl = data.images?.[universityName];

            // Create card
            const card = createUniversityCard(universityName, details, imageUrl, admissionChance, index);
            recommendationsList.appendChild(card);

            // Animate admission chance progress bar
            setTimeout(() => {
                const progressBar = card.querySelector('.progress-bar');
                if (progressBar) progressBar.style.width = `${admissionChance}%`;
            }, (index * 100) + 300);
        } catch (error) {
            console.error(`Error rendering university ${universityName}:`, error);
            // Fallback - simple card
            recommendationsList.appendChild(createSimpleUniversityCard(universityName, data.admission_chances?.[universityName] || '?'));
        }
    });
}

// Check profile completeness and suggest filling missing data
function checkProfileCompleteness() {
    const profileData = collectProfileData();

    // Check necessary academic data
    const missingAcademic = [];

    if (!profileData.academic.gpa) missingAcademic.push('GPA');
    if (!profileData.academic.toeflScore && !profileData.academic.ieltsScore)
        missingAcademic.push('Language test score (TOEFL or IELTS)');

    // Check other important data
    const missingOther = [];

    if (!profileData.personal.specialty) missingOther.push('Specialty');
    if (!profileData.personal.goals) missingOther.push('Goals');
    if (!profileData.personal.skills || profileData.personal.skills.length === 0)
        missingOther.push('Skills');

    // If data is insufficient, show warning
    if (missingAcademic.length > 0 || missingOther.length > 0) {
        let message = 'For better recommendations, please complete your profile:';

        if (missingAcademic.length > 0) {
            message += `\n• Academic info: ${missingAcademic.join(', ')}`;
        }

        if (missingOther.length > 0) {
            message += `\n• Other info: ${missingOther.join(', ')}`;
        }

        showRecommendationNotice(message);
        return false;
    }

    return true;
}

// Show notice in recommendations container
function showRecommendationNotice(message) {
    const recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) return;

    const notice = document.createElement('div');
    notice.className = 'bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4';
    notice.innerHTML = `
        <div class="flex">
            <div class="flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
            </div>
            <div class="ml-3">
                <p class="text-sm text-yellow-700 whitespace-pre-line">${message}</p>
            </div>
        </div>
    `;

    recommendationsList.insertBefore(notice, recommendationsList.firstChild);
}

// Create university card with enhanced UI
function createUniversityCard(universityName, details, imageUrl, admissionChance, index) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-xl shadow-md overflow-hidden mb-6 transition-all duration-300 opacity-0 translate-y-4';
    card.dataset.university = universityName;

    // Get color scheme based on admission chance
    const colorScheme = getAdmissionChanceColorScheme(admissionChance);
    const matchLabel = getAdmissionMatchLabel(admissionChance);

    // Create HTML for the card with added "Learn More" button
    let cardHTML = `
    <div class="relative h-48 w-full overflow-hidden">
      <img src="${imageUrl || 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f'}" 
           alt="${universityName}" class="w-full h-full object-cover transition-transform duration-500 hover:scale-105">
      <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
      <div class="absolute bottom-0 left-0 right-0 p-4">
        <h2 class="text-xl font-bold text-white">${universityName}</h2>
        <p class="text-white/80 flex items-center gap-1 text-sm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          ${details.location || 'Location information unavailable'}
        </p>
      </div>
    </div>
    
    <div class="p-4">
      <div class="flex justify-between items-center mb-4">
        <div class="${colorScheme.badge} px-3 py-1 rounded-full text-sm font-medium inline-flex items-center gap-1">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          ${matchLabel} (${admissionChance}%)
        </div>
        ${details.ranking ? `
          <div class="bg-gray-100 rounded-lg px-2 py-1 text-xs font-medium">
            ${details.ranking}
          </div>
        ` : ''}
      </div>
      
      <div class="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
        <div class="${colorScheme.progressBar} h-full transition-all duration-1000 progress-bar" style="width: 0%"></div>
      </div>
    `;

    // Programs section
    if (details.programs && details.programs.length > 0) {
        cardHTML += `
      <div class="mb-4">
        <h3 class="font-medium text-gray-900 mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M12 14l9-5-9-5-9 5 9 5z" />
            <path d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998a12.078 12.078 0 01.665-6.479L12 14z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998a12.078 12.078 0 01.665-6.479L12 14zm-4 6v-7.5l4-2.222" />
          </svg>
          Relevant Programs
        </h3>
        <ul class="space-y-1 text-sm">
          ${details.programs.slice(0, 3).map(program => `
            <li class="flex items-start gap-2">
              <span class="text-blue-500 mt-0.5">•</span>
              <span>${program}</span>
            </li>
          `).join('')}
          ${details.programs.length > 3 ? `
            <li class="text-xs text-gray-500 pl-4">+${details.programs.length - 3} more programs</li>
          ` : ''}
        </ul>
      </div>
    `;
    }

    // Requirements section
    if (details.requirements && details.requirements.length > 0) {
        cardHTML += `
      <div class="mb-4">
        <h3 class="font-medium text-gray-900 mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          Admission Requirements
        </h3>
        <ul class="space-y-1 text-sm">
          ${details.requirements.slice(0, 3).map(req => `
            <li class="flex items-start gap-2">
              <span class="text-purple-500 mt-0.5">•</span>
              <span>${req}</span>
            </li>
          `).join('')}
          ${details.requirements.length > 3 ? `
            <li class="text-xs text-gray-500 pl-4">+${details.requirements.length - 3} more requirements</li>
          ` : ''}
        </ul>
      </div>
    `;
    }

    // Deadlines section
    if (details.deadlines && details.deadlines.length > 0) {
        cardHTML += `
      <div class="mb-4">
        <h3 class="font-medium text-gray-900 mb-2 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          Application Deadlines
        </h3>
        <ul class="space-y-1 text-sm">
          ${details.deadlines.slice(0, 2).map(deadline => `
            <li class="flex items-start gap-2">
              <span class="text-red-500 mt-0.5">•</span>
              <span>${deadline}</span>
            </li>
          `).join('')}
          ${details.deadlines.length > 2 ? `
            <li class="text-xs text-gray-500 pl-4">+${details.deadlines.length - 2} more deadlines</li>
          ` : ''}
        </ul>
      </div>
    `;
    }

    // Action buttons
    cardHTML += `
    <div class="flex justify-between items-center mt-4 pt-4 border-t border-gray-100">
      <a href="https://www.google.com/search?q=${encodeURIComponent(universityName + ' university')}" 
         target="_blank"
         class="px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-black transition-colors">
        View University
      </a>
      
      <div class="flex space-x-2">
        <button class="learn-more-btn px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                data-university="${universityName}" onclick="getUniversityDetails('${universityName}')">
          Learn More
        </button>
        
        <button class="save-university-btn p-2 text-gray-500 hover:text-blue-600 transition-colors" 
                data-university="${universityName}">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
               d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Expanded University Details Section (Initially Hidden) -->
  <div class="university-details-section hidden px-4 py-5 border-t border-gray-200 space-y-4" id="details-${universityName.replace(/\s+/g, '-').toLowerCase()}">
    <div class="flex justify-between items-center">
      <h3 class="text-lg font-semibold">Detailed Information</h3>
      <button class="close-details-btn p-1 rounded-full hover:bg-gray-100" data-university="${universityName}">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    
    <div class="details-content space-y-4">
      <!-- Content will be dynamically inserted here -->
      <div class="animate-pulse">
        <div class="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div class="h-4 bg-gray-200 rounded w-full mb-2"></div>
        <div class="h-4 bg-gray-200 rounded w-5/6"></div>
      </div>
    </div>
  </div>
    `;

    card.innerHTML = cardHTML;

    // Add event listener for save button
    const saveBtn = card.querySelector('.save-university-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            saveUniversity(this.dataset.university);
        });
    }

    // Add event listener for close details button
    const closeDetailsBtn = card.querySelector('.close-details-btn');
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', function () {
            const university = this.dataset.university;
            const detailsSection = document.getElementById(`details-${university.replace(/\s+/g, '-').toLowerCase()}`);
            if (detailsSection) {
                detailsSection.classList.add('hidden');
            }
        });
    }

    // Animation for appearing
    setTimeout(() => {
        card.classList.remove('opacity-0');
        card.classList.remove('translate-y-4');
    }, index * 100);

    return card;
}

// Get detailed information about a specific university
function getUniversityDetails(universityName) {
    // Find the details section for this university
    const detailsId = `details-${universityName.replace(/\s+/g, '-').toLowerCase()}`;
    const detailsSection = document.getElementById(detailsId);

    if (!detailsSection) {
        console.error(`Details section not found for ${universityName}`);
        return;
    }

    // Show the details section (with loading state)
    detailsSection.classList.remove('hidden');

    // If we already have the details, just show them
    if (expandedUniversityDetails[universityName]) {
        renderUniversityDetails(universityName, expandedUniversityDetails[universityName]);
        return;
    }

    // Otherwise, fetch from server
    const detailsContent = detailsSection.querySelector('.details-content');
    detailsContent.innerHTML = `
        <div class="flex items-center justify-center py-8">
            <div class="w-8 h-8 border-t-4 border-b-4 border-purple-500 rounded-full animate-spin"></div>
            <span class="ml-3 text-sm text-gray-600">Loading detailed information...</span>
        </div>
    `;

    // Get country from select
    const country = document.getElementById('countrySelect').value;

    // Make API request to get detailed university information
    fetch('/get-university-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            university: universityName,
            country: country,
            profile: collectProfileData().personal,
            academic: collectProfileData().academic
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server responded with status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('University details received:', data);

            // Store details for future use
            expandedUniversityDetails[universityName] = data.details;

            // Render the details
            renderUniversityDetails(universityName, data.details);
        })
        .catch(error => {
            console.error(`Error fetching details for ${universityName}:`, error);
            detailsContent.innerHTML = `
            <div class="bg-red-50 p-4 rounded-lg">
                <p class="text-red-600">Error loading details: ${error.message}</p>
                <button class="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700" 
                        onclick="getUniversityDetails('${universityName}')">
                    Try Again
                </button>
            </div>
        `;
        });
}

// Render detailed university information
function renderUniversityDetails(universityName, details) {
    const detailsId = `details-${universityName.replace(/\s+/g, '-').toLowerCase()}`;
    const detailsSection = document.getElementById(detailsId);

    if (!detailsSection) return;

    const detailsContent = detailsSection.querySelector('.details-content');

    // Create HTML content from details
    let detailsHTML = '';

    // Admission & Selectivity
    if (details.admissions) {
        detailsHTML += `
        <div class="p-4 bg-blue-50 rounded-lg">
            <h4 class="font-semibold text-blue-800 mb-2">Admission & Selectivity</h4>
            <ul class="space-y-2 text-sm">
                ${details.admissions.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // Costs & Financial Aid
    if (details.costs) {
        detailsHTML += `
        <div class="p-4 bg-green-50 rounded-lg">
            <h4 class="font-semibold text-green-800 mb-2">Costs & Financial Aid</h4>
            <ul class="space-y-2 text-sm">
                ${details.costs.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-green-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // Academic Programs
    if (details.programs) {
        detailsHTML += `
        <div class="p-4 bg-purple-50 rounded-lg">
            <h4 class="font-semibold text-purple-800 mb-2">Notable Academic Programs</h4>
            <ul class="space-y-2 text-sm">
                ${details.programs.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-purple-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // Campus Life
    if (details.campusLife) {
        detailsHTML += `
        <div class="p-4 bg-yellow-50 rounded-lg">
            <h4 class="font-semibold text-yellow-800 mb-2">Campus Life & Student Experience</h4>
            <ul class="space-y-2 text-sm">
                ${details.campusLife.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-yellow-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // Career Outcomes
    if (details.careers) {
        detailsHTML += `
        <div class="p-4 bg-red-50 rounded-lg">
            <h4 class="font-semibold text-red-800 mb-2">Career Outcomes & Job Placement</h4>
            <ul class="space-y-2 text-sm">
                ${details.careers.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-red-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // For You / Personalized Section
    if (details.personalized) {
        detailsHTML += `
        <div class="p-4 bg-indigo-50 rounded-lg">
            <h4 class="font-semibold text-indigo-800 mb-2">Why This University Is For You</h4>
            <ul class="space-y-2 text-sm">
                ${details.personalized.map(item => `
                <li class="flex items-start gap-2">
                    <svg class="h-4 w-4 text-indigo-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                    </svg>
                    <span>${item}</span>
                </li>`).join('')}
            </ul>
        </div>`;
    }

    // Add link to application at bottom
    detailsHTML += `
    <div class="p-4 bg-gray-50 rounded-lg text-center">
        <a href="https://www.google.com/search?q=${encodeURIComponent(universityName + ' apply admission')}" 
           target="_blank"
           class="px-4 py-2 bg-black text-white rounded-lg inline-flex items-center gap-2 hover:bg-gray-800 transition-colors">
           <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
           Apply Now
        </a>
    </div>`;

    // Update the content
    detailsContent.innerHTML = detailsHTML;
}

// Show/hide recommendations container based on state
function showRecommendationsContainer() {
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const recommendationsContainer = document.getElementById('recommendationsContainer');

    if (loadingState) loadingState.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
    if (recommendationsContainer) recommendationsContainer.style.display = 'block';
}

// Create a simple university card (fallback)
function createSimpleUniversityCard(universityName, admissionChance) {
    const card = document.createElement('div');
    card.className = 'bg-white rounded-lg shadow-sm p-6 mb-4';
    card.innerHTML = `
    <h3 class="text-lg font-bold">${universityName}</h3>
    <p class="text-sm text-gray-500 mb-2">Could not load detailed information</p>
    <p class="text-sm">Admission chance: ${admissionChance || 'Unknown'}%</p>
    <div class="flex justify-between items-center mt-4">
        <a href="https://www.google.com/search?q=${encodeURIComponent(universityName + ' university')}" 
           target="_blank" class="text-blue-600 hover:underline text-sm">
           Learn more about this university
        </a>
        <button class="save-university-btn p-2 text-gray-500 hover:text-blue-600 transition-colors" 
                data-university="${universityName}">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                   d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
            </svg>
        </button>
    </div>
    `;

    // Add save button handler
    const saveBtn = card.querySelector('.save-university-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            saveUniversity(this.dataset.university);
        });
    }

    return card;
}

// Extract university details from recommendation text
function extractUniversityDetails(text, universityName) {
    if (!text) return {
        location: '',
        programs: [],
        requirements: [],
        strengths: [],
        costs: [],
        deadlines: [],
        ranking: ''
    };

    const details = {
        location: '',
        programs: [],
        requirements: [],
        strengths: [],
        costs: [],
        deadlines: [],
        ranking: ''
    };

    const lines = text.split('\n');
    let inUniversity = false;
    let currentSection = null;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        // Check if this is the start of a university section
        if (line.includes(`**University: ${universityName}**`) || line.includes(`**University:${universityName}**`)) {
            inUniversity = true;
            continue;
        }

        // Check if we've moved to the next university
        if (inUniversity && line.includes('**University:') && !line.includes(universityName)) {
            break;
        }

        // Process the line if we're in the correct university section
        if (inUniversity) {
            // Check section headers
            if (line.startsWith('**Location:**')) {
                currentSection = 'location';
                details.location = line.replace('**Location:**', '').trim();
            } else if (line.startsWith('**Relevant Programs:**')) {
                currentSection = 'programs';
            } else if (line.startsWith('**Admission Requirements:**')) {
                currentSection = 'requirements';
            } else if (line.startsWith('**Application Deadlines:**')) {
                currentSection = 'deadlines';
            } else if (line.startsWith('**Estimated Costs:**')) {
                currentSection = 'costs';
            } else if (line.startsWith('**Notable Strengths:**')) {
                currentSection = 'strengths';
            } else if (line.startsWith('**QS World Ranking:**')) {
                currentSection = 'ranking';
                details.ranking = line.replace('**QS World Ranking:**', '').trim();
            } else if (line.startsWith('*') && line.length > 2) {
                // This is a bullet point in a section
                const content = line.substring(1).trim();
                if (currentSection && currentSection !== 'location' && currentSection !== 'ranking') {
                    details[currentSection].push(content);
                }
            }
        }
    }

    return details;
}

// Get color scheme based on admission chance
function getAdmissionChanceColorScheme(chance) {
    if (chance >= 80) {
        return {
            badge: 'bg-green-100 text-green-800',
            progressBar: 'bg-green-500',
            text: 'text-green-700'
        };
    } else if (chance >= 60) {
        return {
            badge: 'bg-blue-100 text-blue-800',
            progressBar: 'bg-blue-500',
            text: 'text-blue-700'
        };
    } else if (chance >= 40) {
        return {
            badge: 'bg-yellow-100 text-yellow-800',
            progressBar: 'bg-yellow-500',
            text: 'text-yellow-700'
        };
    } else {
        return {
            badge: 'bg-red-100 text-red-800',
            progressBar: 'bg-red-500',
            text: 'text-red-700'
        };
    }
}

// Get label for admission chance
function getAdmissionMatchLabel(chance) {
    if (chance >= 80) return 'Excellent Match';
    if (chance >= 60) return 'Good Match';
    if (chance >= 40) return 'Moderate Match';
    return 'Challenging Match';
}

// Save university to favorites
function saveUniversity(universityName) {
    try {
        // Check if localStorage is available
        if (!window.localStorage) {
            showNotification('Your browser does not support saving favorites', 'error');
            return;
        }

        // Get existing saved universities
        let savedUniversities = JSON.parse(localStorage.getItem('savedUniversities') || '[]');

        // Check if university is already saved
        if (savedUniversities.includes(universityName)) {
            showNotification(`${universityName} is already in your favorites`);
            return;
        }

        // Add university and save
        savedUniversities.push(universityName);
        localStorage.setItem('savedUniversities', JSON.stringify(savedUniversities));

        // Update save button icon
        const saveBtn = document.querySelector(`.save-university-btn[data-university="${universityName}"]`);
        if (saveBtn) {
            saveBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="currentColor" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
            `;
        }

        showNotification(`Added ${universityName} to favorites`);
    } catch (error) {
        console.error('Error saving university:', error);
        showNotification('Could not save university', 'error');
    }
}

// Load saved universities
function loadSavedUniversities() {
    if (!window.localStorage) {
        return [];
    }

    try {
        return JSON.parse(localStorage.getItem('savedUniversities') || '[]');
    } catch (error) {
        console.error('Error loading saved universities:', error);
        return [];
    }
}

// Show saved universities
function showSavedUniversities() {
    const recommendationsList = document.getElementById('recommendationsList');
    if (!recommendationsList) return;

    // Clear list
    recommendationsList.innerHTML = '';

    // Get saved universities
    const savedUniversities = loadSavedUniversities();

    if (savedUniversities.length === 0) {
        recommendationsList.innerHTML = `
            <div class="bg-white rounded-lg shadow-sm p-6 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                <h3 class="text-lg font-medium text-gray-700 mb-2">No Saved Universities</h3>
                <p class="text-gray-500 mb-4">When you save universities, they will appear here</p>
            </div>
        `;
        return;
    }

    // Create card for each saved university
    savedUniversities.forEach((universityName, index) => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-sm p-4 mb-4 flex justify-between items-center opacity-0 translate-y-4 transition-all duration-300';

        card.innerHTML = `
            <div>
                <h3 class="font-semibold text-lg">${universityName}</h3>
                <p class="text-sm text-gray-600">Saved University</p>
            </div>
            <div class="flex space-x-2">
                <a href="https://www.google.com/search?q=${encodeURIComponent(universityName + ' university')}" 
                   target="_blank"
                   class="p-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                           d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                </a>
                <button class="p-2 text-red-500 border border-red-200 rounded-lg hover:bg-red-50 transition-colors remove-university-btn"
                        data-university="${universityName}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                           d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
            </div>
        `;

        // Add handler for remove button
        const removeBtn = card.querySelector('.remove-university-btn');
        if (removeBtn) {
            removeBtn.addEventListener('click', function () {
                removeFromFavorites(this.dataset.university);
            });
        }

        recommendationsList.appendChild(card);

        // Appearance animation
        setTimeout(() => {
            card.classList.remove('opacity-0');
            card.classList.remove('translate-y-4');
        }, index * 100);
    });

    // Show results container
    const recommendationsContainer = document.getElementById('recommendationsContainer');
    if (recommendationsContainer) {
        recommendationsContainer.style.display = 'block';
    }

    // Hide other states
    const loadingState = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');

    if (loadingState) loadingState.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
}

// Remove university from favorites
function removeFromFavorites(universityName) {
    if (!window.localStorage) {
        return;
    }

    try {
        // Get existing favorites
        const savedUniversities = JSON.parse(localStorage.getItem('savedUniversities') || '[]');

        // Remove university
        const index = savedUniversities.indexOf(universityName);
        if (index !== -1) {
            savedUniversities.splice(index, 1);
            localStorage.setItem('savedUniversities', JSON.stringify(savedUniversities));

            showNotification(`Removed ${universityName} from favorites`);

            // Update display
            showSavedUniversities();
        }
    } catch (error) {
        console.error('Error removing university:', error);
        showNotification('Could not remove university', 'error');
    }
}

// Ensure admission chances are available 
function ensureAdmissionChances(data) {
    if (!data.admission_chances || Object.keys(data.admission_chances).length === 0) {
        console.log('Server did not provide admission chances, generating fallbacks');
        data.admission_chances = generateRandomAdmissionChances(data.universities || []);
    }
    return data;
}

// Generate random admission chances for testing
function generateRandomAdmissionChances(universities) {
    const eliteUniversities = [
        'Harvard', 'Stanford', 'MIT', 'Oxford', 'Cambridge', 'Princeton',
        'Yale', 'Columbia', 'Caltech', 'Chicago', 'Imperial College'
    ];

    const prestigiousUniversities = [
        'UCLA', 'Berkeley', 'NYU', 'Michigan', 'Toronto', 'LSE',
        'Edinburgh', 'UCL', 'Sydney', 'Melbourne', 'ETH Zurich'
    ];

    const chances = {};

    universities.forEach(uni => {
        if (eliteUniversities.some(elite => uni.includes(elite))) {
            // Elite universities - low chances
            chances[uni] = Math.floor(Math.random() * 15) + 25; // 25-40%
        } else if (prestigiousUniversities.some(prestige => uni.includes(prestige))) {
            // Prestigious universities - medium chances
            chances[uni] = Math.floor(Math.random() * 20) + 40; // 40-60%
        } else {
            // Other universities - high chances
            chances[uni] = Math.floor(Math.random() * 25) + 60; // 60-85%
        }
    });

    return chances;
}

// Setup recommendations tab buttons
function setupRecommendationTabs() {
    const recommendationsTabBtn = document.getElementById('recommendationsTabBtn');
    const favoritesTabBtn = document.getElementById('favoritesTabBtn');

    if (recommendationsTabBtn && favoritesTabBtn) {
        // Show recommendations
        recommendationsTabBtn.addEventListener('click', switchToRecommendationsTab);

        // Show favorites
        favoritesTabBtn.addEventListener('click', switchToFavoritesTab);
    }
}

// Switch to recommendations tab
function switchToRecommendationsTab() {
    const recommendationsTabBtn = document.getElementById('recommendationsTabBtn');
    const favoritesTabBtn = document.getElementById('favoritesTabBtn');

    if (recommendationsTabBtn && favoritesTabBtn) {
        recommendationsTabBtn.className = 'px-4 py-2 font-medium text-black border-b-2 border-black';
        favoritesTabBtn.className = 'px-4 py-2 font-medium text-gray-500 hover:text-black';

        // If we have saved recommendations, show them without making a new request
        if (currentRecommendationResults) {
            showRecommendationsContainer();
            renderRecommendations(currentRecommendationResults);
        } else {
            // Check if there are already displayed recommendations
            const existingRecommendations = document.querySelector('#recommendationsList .bg-white');
            if (existingRecommendations) {
                showRecommendationsContainer();
            } else {
                // Only if we have nothing to show, make a new request
                getRecommendations();
            }
        }
    }
}

// Switch to favorites tab
function switchToFavoritesTab() {
    const recommendationsTabBtn = document.getElementById('recommendationsTabBtn');
    const favoritesTabBtn = document.getElementById('favoritesTabBtn');

    if (recommendationsTabBtn && favoritesTabBtn) {
        favoritesTabBtn.className = 'px-4 py-2 font-medium text-black border-b-2 border-black';
        recommendationsTabBtn.className = 'px-4 py-2 font-medium text-gray-500 hover:text-black';

        showSavedUniversities();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    console.log('Enhanced recommendations JS loaded');

    // Setup tab buttons
    setupRecommendationTabs();

    // Setup event handlers for country select
    const countrySelect = document.getElementById('countrySelect');
    if (countrySelect) {
        countrySelect.addEventListener('change', function () {
            const findButton = document.querySelector('button[onclick="getRecommendations()"]') ||
                document.querySelector('#find-universities-btn');

            if (findButton) {
                findButton.disabled = !this.value;
                findButton.classList.toggle('opacity-50', !this.value);
                findButton.classList.toggle('cursor-not-allowed', !this.value);
            }
        });
    }

    // Setup profile header toggle
    const profileHeader = document.getElementById('profileHeader');
    if (profileHeader) {
        profileHeader.addEventListener('click', function () {
            const profileSection = document.getElementById('profileOverview');
            const profileToggle = document.getElementById('profileToggleIcon');

            if (profileSection && profileToggle) {
                const isVisible = profileSection.style.display !== 'none';
                profileSection.style.display = isVisible ? 'none' : 'block';
                profileToggle.classList.toggle('rotate-180', isVisible);
            }
        });
    }
});

// Show notification
function showNotification(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-md text-white ${type === 'error' ? 'bg-red-500' : 'bg-green-500'} shadow-lg z-50`;
    toast.innerHTML = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}