/**
 * Universal AI Library Assistant - Frontend Client
 * Handles chat communication with local Ollama (Llama 3.2 3B),
 * conversation history, verified catalogue grounding, multi-tier filtering,
 * and comprehensive Book Details modal viewer for all library resources.
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    const conversationHistory = [];
    let isWaitingForAi = false;
    const loadedResourcesMap = new Map();

    // DOM Elements - Chat
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const suggestionChips = document.querySelectorAll('.chip-btn');

    // DOM Elements - Catalogue
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const eduLevelFilter = document.getElementById('eduLevelFilter');
    const subjectFilter = document.getElementById('subjectFilter');
    const levelFilter = document.getElementById('levelFilter');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    const resourcesGrid = document.getElementById('resourcesGrid');
    const catalogCounter = document.getElementById('catalogCounter');

    // DOM Elements - Book Details Modal
    const bookModalBackdrop = document.getElementById('bookModalBackdrop');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalCloseFooterBtn = document.getElementById('modalCloseFooterBtn');
    const modalBody = document.getElementById('modalBody');
    const modalHeaderTitle = document.getElementById('modalHeaderTitle');

    // DOM Elements - Header & Mobile
    const statusText = document.getElementById('statusText');
    const statusDot = document.querySelector('.status-dot');
    const mobileTabs = document.querySelectorAll('.mobile-tabs .tab-btn');
    const chatSection = document.getElementById('chatSection');
    const catalogSection = document.getElementById('catalogSection');

    // ------------------------------------------------------------------------
    // 1. Initialise System & Data
    // ------------------------------------------------------------------------

    async function checkHealth() {
        try {
            const res = await fetch('/api/health');
            if (!res.ok) throw new Error('Health check response not ok');
            const data = await res.json();

            if (data.ai_connected && data.model_available) {
                statusDot.className = 'status-dot online';
                statusText.textContent = `Ollama Active (${data.model || 'llama3.2:3b'})`;
                statusText.title = `Connected to Ollama at ${data.ollama_url} running ${data.model}`;
            } else if (data.ai_connected && !data.model_available) {
                statusDot.className = 'status-dot warning';
                statusText.textContent = `Model Missing: ${data.model}`;
                statusText.title = `Ollama is running, but '${data.model}' is not pulled yet. Run: ollama run ${data.model}`;
            } else {
                statusDot.className = 'status-dot warning';
                statusText.textContent = 'Ollama Offline (Start Ollama)';
                statusText.title = `Ollama not detected at ${data.ollama_url || 'http://localhost:11434'}. Start Ollama to enable AI chat.`;
            }
        } catch (err) {
            statusDot.className = 'status-dot';
            statusText.textContent = 'Server Offline';
        }
    }

    async function loadSubjects() {
        try {
            const res = await fetch('/api/subjects');
            if (!res.ok) throw new Error('Failed to load subjects');
            const data = await res.json();
            const subjects = data.subjects || [];

            subjectFilter.innerHTML = '<option value="">All Subjects</option>';
            subjects.forEach(sub => {
                const opt = document.createElement('option');
                opt.value = sub;
                opt.textContent = sub;
                subjectFilter.appendChild(opt);
            });
        } catch (err) {
            console.error('Error fetching subjects:', err);
        }
    }

    async function fetchResources() {
        const q = searchInput.value.trim();
        const eduLevel = eduLevelFilter ? eduLevelFilter.value : '';
        const subject = subjectFilter ? subjectFilter.value : '';
        const level = levelFilter ? levelFilter.value : '';

        const params = new URLSearchParams();
        if (q) params.append('q', q);
        if (eduLevel) params.append('education_level', eduLevel);
        if (subject) params.append('subject', subject);
        if (level) params.append('level', level);

        catalogCounter.textContent = 'Searching...';

        try {
            const res = await fetch(`/api/resources?${params.toString()}`);
            if (!res.ok) throw new Error('Failed to fetch resources');
            const data = await res.json();
            const items = data.resources || [];

            // Update in-memory cache
            loadedResourcesMap.clear();
            items.forEach(item => {
                if (item.id != null) {
                    loadedResourcesMap.set(Number(item.id), item);
                }
            });

            renderResources(items);
        } catch (err) {
            console.error('Error fetching resources:', err);
            resourcesGrid.innerHTML = `
                <div class="alert-box alert-error">
                    <span>⚠️ Error loading resources. Please check server connection.</span>
                </div>
            `;
            catalogCounter.textContent = 'Error';
        }
    }

    function renderResources(resources) {
        catalogCounter.textContent = `${resources.length} resource${resources.length === 1 ? '' : 's'}`;

        if (resources.length === 0) {
            resourcesGrid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <p><strong>No resources found</strong></p>
                    <p>Try clearing your filters or searching for another subject, class, or keyword.</p>
                </div>
            `;
            return;
        }

        resourcesGrid.innerHTML = resources.map(r => {
            const levelClass = r.level ? `tag-level-${r.level.toLowerCase()}` : '';
            const eduTag = r.education_level ? `<span class="tag tag-edu">${escapeHtml(r.education_level)}</span>` : '';
            const classTag = r.class_grade && r.class_grade !== 'All Classes' ? `<span class="tag tag-subject">${escapeHtml(r.class_grade)}</span>` : '';
            const langTag = r.language && r.language.toLowerCase() === 'kannada' ? `<span class="tag tag-kannada">ಕನ್ನಡ</span>` : '';
            const publisherTag = r.publisher ? `<div class="card-publisher">Publisher: ${escapeHtml(r.publisher)}</div>` : '';

            const hasUrl = r.url && r.url.trim() !== '';
            let actionButtons = '';
            if (hasUrl) {
                actionButtons = `
                    <button type="button" class="card-details-btn action-details-btn" data-id="${r.id}" title="View book details">
                        Details
                    </button>
                    <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="card-link-btn action-view-resource" title="Open verified resource in new tab">
                        <span>View Resource</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </a>
                `;
            } else {
                actionButtons = `
                    <button type="button" class="card-link-btn card-details-btn action-details-btn" data-id="${r.id}" title="View complete book information">
                        <span>View Book Details</span>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                    </button>
                `;
            }

            return `
                <div class="resource-card" data-id="${r.id}" tabindex="0" role="button" aria-label="View details for ${escapeHtml(r.title)}">
                    <div class="card-top">
                        <div class="card-tags">
                            ${eduTag}
                            ${classTag}
                            <span class="tag tag-subject">${escapeHtml(r.subject || 'General')}</span>
                            ${langTag}
                            <span class="tag ${levelClass}">${escapeHtml(r.level || 'All Levels')}</span>
                            <span class="tag tag-type">${escapeHtml(r.resource_type || 'Book')}</span>
                        </div>
                    </div>
                    <div class="card-title">${escapeHtml(r.title)}</div>
                    <div class="card-author">by ${escapeHtml(r.author || 'Unknown Author')}</div>
                    ${publisherTag}
                    <div class="card-desc">${escapeHtml(r.description || '')}</div>
                    <div class="card-actions">
                        ${actionButtons}
                    </div>
                </div>
            `;
        }).join('');

        // Attach click listeners to cards and actions
        resourcesGrid.querySelectorAll('.resource-card').forEach(card => {
            const resId = Number(card.getAttribute('data-id'));
            const resData = loadedResourcesMap.get(resId);

            card.addEventListener('click', (e) => {
                // If clicked on external link "View Resource", let it open in a new tab normally without modal
                if (e.target.closest('.action-view-resource')) {
                    return;
                }
                openBookModal(resData || { id: resId });
            });

            // Keyboard accessibility (Enter or Space)
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    if (!e.target.closest('.action-view-resource')) {
                        e.preventDefault();
                        openBookModal(resData || { id: resId });
                    }
                }
            });
        });
    }

    // ------------------------------------------------------------------------
    // 2. Book Details Modal Functionality
    // ------------------------------------------------------------------------

    async function openBookModal(r) {
        if (!r) return;

        // If data is minimal (e.g. only ID), fetch full record from API
        let fullResource = r;
        if (!r.title && r.id) {
            try {
                const res = await fetch(`/api/resources/${r.id}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.resource) fullResource = data.resource;
                }
            } catch (err) {
                console.error('Error fetching resource details:', err);
            }
        }

        const hasUrl = fullResource.url && fullResource.url.trim() !== '';
        const gradeText = fullResource.class_grade && fullResource.class_grade !== 'All Classes' ? fullResource.class_grade : 'All Classes / Not Specified';
        const publisherText = fullResource.publisher && fullResource.publisher.trim() !== '' ? fullResource.publisher : 'Official Academic Curriculum / University Press';

        modalHeaderTitle.textContent = fullResource.resource_type ? `${fullResource.resource_type} Details` : 'Book Details';

        let availabilityHtml = '';
        if (hasUrl) {
            availabilityHtml = `
                <div class="modal-availability-box online">
                    <div class="availability-status-title">
                        <span>✅</span> <span>Verified Official Resource Available</span>
                    </div>
                    <p class="availability-desc">This textbook or reference material is available to view directly online from the verified official educational publisher.</p>
                    <a href="${escapeHtml(fullResource.url)}" target="_blank" rel="noopener noreferrer" class="primary-btn modal-external-link-btn" title="Open verified external link in new tab">
                        <span>View / Open Resource</span>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                    </a>
                </div>
            `;
        } else {
            availabilityHtml = `
                <div class="modal-availability-box library-only">
                    <div class="availability-status-title">
                        <span>🏛️</span> <span>Available in Physical Library Collection</span>
                    </div>
                    <p class="availability-desc">This edition is part of the college library physical collection and reference stacks. You can access it on campus under the <strong>${escapeHtml(fullResource.subject || 'General')}</strong> section or request loan access from the circulation desk.</p>
                </div>
            `;
        }

        modalBody.innerHTML = `
            <div class="book-detail-hero">
                <div class="book-detail-title">${escapeHtml(fullResource.title || 'Untitled Book')}</div>
                <div class="book-detail-author">by ${escapeHtml(fullResource.author || 'Unknown Author')}</div>
                <div class="book-detail-publisher"><strong>Publisher:</strong> ${escapeHtml(publisherText)}</div>
            </div>

            <div class="modal-metadata-grid">
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Subject</span>
                    <span class="modal-meta-val">${escapeHtml(fullResource.subject || 'General')}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Education Level</span>
                    <span class="modal-meta-val">${escapeHtml(fullResource.education_level || 'All Levels')}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Class / Grade</span>
                    <span class="modal-meta-val">${escapeHtml(gradeText)}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Difficulty</span>
                    <span class="modal-meta-val">${escapeHtml(fullResource.level || 'All Levels')}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Department</span>
                    <span class="modal-meta-val">${escapeHtml(fullResource.department || 'General')}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Language</span>
                    <span class="modal-meta-val">${escapeHtml(fullResource.language || 'English')}</span>
                </div>
            </div>

            <div class="book-detail-section">
                <h4>Book Description</h4>
                <p>${escapeHtml(fullResource.description || 'No detailed description provided.')}</p>
            </div>

            <div class="book-detail-section">
                <h4>Access &amp; Availability</h4>
                ${availabilityHtml}
            </div>
        `;

        bookModalBackdrop.style.display = 'flex';
        bookModalBackdrop.setAttribute('aria-hidden', 'false');
    }

    function closeBookModal() {
        bookModalBackdrop.style.display = 'none';
        bookModalBackdrop.setAttribute('aria-hidden', 'true');
    }

    if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeBookModal);
    if (modalCloseFooterBtn) modalCloseFooterBtn.addEventListener('click', closeBookModal);
    if (bookModalBackdrop) {
        bookModalBackdrop.addEventListener('click', (e) => {
            if (e.target === bookModalBackdrop) {
                closeBookModal();
            }
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && bookModalBackdrop && bookModalBackdrop.style.display !== 'none') {
            closeBookModal();
        }
    });

    // ------------------------------------------------------------------------
    // 3. Chat Assistant Functionality
    // ------------------------------------------------------------------------

    function formatMessageContent(text) {
        let html = escapeHtml(text);

        // Bold **text**
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Numbered list item: e.g. "1. Item"
        html = html.replace(/^(\d+)\.\s+(.*)$/gm, '<li><strong>$1.</strong> $2</li>');

        // Bullet list item: e.g. "- Item" or "* Item"
        html = html.replace(/^[-*]\s+(.*)$/gm, '<li>$1</li>');

        // Wrap list items in <ul> or <ol>
        html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

        // Convert double newlines to paragraph breaks
        html = html.replace(/\n\n+/g, '</p><p>');

        // Convert single newlines to <br>
        html = html.replace(/\n/g, '<br>');

        return `<p>${html}</p>`;
    }

    function appendMessage(role, content, recommendedResources = null, catalogueNote = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'assistant') {
            contentDiv.innerHTML = formatMessageContent(content);

            // 1. If genuine catalogue resources were matched, display quick reference cards
            if (recommendedResources && recommendedResources.length > 0) {
                const recContainer = document.createElement('div');
                recContainer.className = 'recommended-cards-container';
                
                const recLabel = document.createElement('div');
                recLabel.style.fontSize = '0.75rem';
                recLabel.style.fontWeight = '600';
                recLabel.style.color = '#4f46e5';
                recLabel.style.marginTop = '8px';
                recLabel.textContent = 'Referenced Catalogue Items (Verified Library Resources):';
                recContainer.appendChild(recLabel);

                recommendedResources.forEach(res => {
                    const chip = document.createElement('div');
                    chip.className = 'rec-card-chip';
                    const gradePart = res.class_grade && res.class_grade !== 'All Classes' ? ` &bull; ${res.class_grade}` : '';
                    const eduPart = res.education_level ? ` &bull; ${res.education_level}` : '';
                    const pubPart = res.publisher ? ` &bull; ${res.publisher}` : '';
                    chip.innerHTML = `
                        <div class="rec-card-title">📖 ${escapeHtml(res.title)}</div>
                        <div class="rec-card-meta">by ${escapeHtml(res.author)}${eduPart}${gradePart}${pubPart} &bull; ${escapeHtml(res.subject)}</div>
                    `;
                    chip.style.cursor = 'pointer';
                    chip.title = 'Click to view complete book details';
                    chip.addEventListener('click', () => {
                        openBookModal(res);
                    });
                    recContainer.appendChild(chip);
                });
                contentDiv.appendChild(recContainer);
            } else if (catalogueNote) {
                // 2. If no matching catalogue books were found, clearly display the honest note
                const noteDiv = document.createElement('div');
                noteDiv.className = 'catalogue-empty-note';
                noteDiv.innerHTML = `<span>ℹ️</span> <span>${escapeHtml(catalogueNote)}</span>`;
                contentDiv.appendChild(noteDiv);
            }
        } else {
            const p = document.createElement('p');
            p.textContent = content;
            contentDiv.appendChild(p);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendSystemNotice(title, message, isWarning = true) {
        const noticeDiv = document.createElement('div');
        noticeDiv.className = `alert-box ${isWarning ? 'alert-warning' : 'alert-error'}`;
        noticeDiv.innerHTML = `
            <div>
                <strong>${escapeHtml(title)}</strong>
                <p style="margin-top: 4px;">${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(noticeDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleSendMessage(messageText) {
        const text = (messageText || chatInput.value).trim();
        if (!text || isWaitingForAi) return;

        // Display user message in conversation
        appendMessage('user', text);
        chatInput.value = '';
        isWaitingForAi = true;
        sendBtn.disabled = true;
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    history: conversationHistory,
                }),
            });

            const data = await response.json();

            typingIndicator.style.display = 'none';

            if (response.ok && data.success) {
                // Successful AI reply (or domain rejection message)
                appendMessage('assistant', data.reply, data.recommended_resources, data.catalogue_note);

                // Update conversation history (limit to last 10 messages)
                conversationHistory.push({ role: 'user', content: text });
                conversationHistory.push({ role: 'assistant', content: data.reply });
                if (conversationHistory.length > 10) {
                    conversationHistory.splice(0, conversationHistory.length - 10);
                }
            } else if (data.error_type === 'ollama_not_running') {
                appendSystemNotice(
                    'Ollama Not Running',
                    data.message || 'Ollama is not running. Start Ollama with `ollama serve` or launch the Ollama app.',
                    true
                );
            } else if (data.error_type === 'model_missing') {
                appendSystemNotice(
                    'Ollama Model Missing',
                    data.message || 'The model llama3.2:3b is missing. Download it by running: `ollama run llama3.2:3b`',
                    true
                );
            } else if (data.error_type === 'timeout') {
                appendSystemNotice(
                    'Generation Timeout',
                    data.message || 'The local model took too long to generate a response. Please try again.',
                    true
                );
            } else {
                appendSystemNotice(
                    'Assistant Notice',
                    data.message || data.error || 'An error occurred while generating a response.',
                    false
                );
            }
        } catch (err) {
            typingIndicator.style.display = 'none';
            appendSystemNotice(
                'Connection Error',
                'Could not connect to the Flask server. Please make sure the Flask application is running.',
                false
            );
        } finally {
            isWaitingForAi = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    // ------------------------------------------------------------------------
    // 4. Event Listeners
    // ------------------------------------------------------------------------

    // Chat submit
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        handleSendMessage();
    });

    // Clear chat
    clearChatBtn.addEventListener('click', () => {
        conversationHistory.length = 0;
        chatMessages.innerHTML = `
            <div class="message assistant-message">
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <p>Chat cleared! What academic subject, class, or learning topic would you like help with? (ಕನ್ನಡದಲ್ಲೂ ಕೇಳಬಹುದು)</p>
                </div>
            </div>
        `;
    });

    // Suggestion chips click
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            if (query) {
                handleSendMessage(query);
            }
        });
    });

    // Catalogue search input with debounce
    let searchDebounceTimeout = null;
    searchInput.addEventListener('input', () => {
        clearSearchBtn.style.display = searchInput.value ? 'block' : 'none';
        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
            fetchResources();
        }, 300);
    });

    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        fetchResources();
    });

    // Filter dropdowns
    if (eduLevelFilter) eduLevelFilter.addEventListener('change', fetchResources);
    if (subjectFilter) subjectFilter.addEventListener('change', fetchResources);
    if (levelFilter) levelFilter.addEventListener('change', fetchResources);

    resetFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.style.display = 'none';
        if (eduLevelFilter) eduLevelFilter.value = '';
        if (subjectFilter) subjectFilter.value = '';
        if (levelFilter) levelFilter.value = '';
        fetchResources();
    });

    // Mobile tabs switcher
    function switchToCatalogTab() {
        if (window.innerWidth <= 960) {
            mobileTabs.forEach(b => b.classList.remove('active'));
            const catBtn = document.querySelector('[data-tab="catalogSection"]');
            if (catBtn) catBtn.classList.add('active');
            chatSection.classList.remove('active-tab');
            catalogSection.classList.add('active-tab');
        }
    }

    mobileTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            mobileTabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (targetTab === 'chatSection') {
                chatSection.classList.add('active-tab');
                catalogSection.classList.remove('active-tab');
            } else {
                chatSection.classList.remove('active-tab');
                catalogSection.classList.add('active-tab');
            }
        });
    });

    // Utility: HTML Escaper to prevent XSS
    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Initialise on load
    checkHealth();
    loadSubjects();
    fetchResources();
});
