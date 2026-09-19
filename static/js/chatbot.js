// ReTurn Platform - Career Assistant Chatbox Widget
document.addEventListener('DOMContentLoaded', () => {
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotToggleBtn = document.getElementById('chatbot-toggle-btn');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotCloseBtn = document.getElementById('chatbot-close-btn');
    const chatbotForm = document.getElementById('chatbot-form');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotMessages = document.getElementById('chatbot-messages');

    if (!chatbotContainer || !chatbotToggleBtn || !chatbotWindow || !chatbotCloseBtn) {
        return;
    }

    // Open Chatbot Window
    function openChatbot() {
        chatbotWindow.classList.remove('hidden');
        chatbotToggleBtn.classList.add('hidden');
        if (chatbotInput) {
            setTimeout(() => chatbotInput.focus(), 50);
        }
        scrollToBottom();
    }

    // Close Chatbot Window (Triggered by Cross / "Wrong" Button, Esc key, etc.)
    function closeChatbot() {
        chatbotWindow.classList.add('hidden');
        chatbotToggleBtn.classList.remove('hidden');
        chatbotToggleBtn.focus();
    }

    // Toggle on launcher button click
    chatbotToggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        openChatbot();
    });

    // Close on clicking the cross / "wrong" button (❌)
    chatbotCloseBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        closeChatbot();
    });

    // Close on Escape key if chatbot window is open
    document.addEventListener('keydown', (e) => {
        if ((e.key === 'Escape' || e.key === 'Esc') && !chatbotWindow.classList.contains('hidden')) {
            closeChatbot();
        }
    });

    // Handle Quick Suggestion Chips
    const chips = document.querySelectorAll('.chat-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const questionText = chip.textContent.trim();
            if (chatbotInput && questionText) {
                chatbotInput.value = questionText;
                submitUserMessage(questionText);
            }
        });
    });

    // Handle Form Submit
    if (chatbotForm && chatbotInput) {
        chatbotForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = chatbotInput.value.trim();
            if (!text) return;
            submitUserMessage(text);
        });
    }

    function scrollToBottom() {
        if (chatbotMessages) {
            chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        }
    }

    // Safe Markdown Formatter
    function formatMarkdown(text) {
        if (!text) return '';
        // Escape HTML
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Bold
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
        // Italics
        escaped = escaped.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
        // Links: [text](url)
        escaped = escaped.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" class="text-teal-700 underline font-medium hover:text-teal-900" target="_blank" rel="noopener">$1</a>');
        // Bullets / lists
        escaped = escaped.replace(/^• (.*?)$/gm, '<li class="ml-4 list-disc">$1</li>');
        // New lines
        escaped = escaped.replace(/\n\n/g, '<div class="h-2"></div>');
        escaped = escaped.replace(/\n/g, '<br>');

        return escaped;
    }

    async function submitUserMessage(userText) {
        chatbotInput.value = '';

        // Append user message bubble
        const userBubble = document.createElement('div');
        userBubble.className = 'flex justify-end';
        userBubble.innerHTML = `
            <div class="bg-teal-700 text-white p-2.5 rounded-lg shadow-2xs max-w-[85%] text-[11.5px] leading-relaxed">
                ${userText.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
            </div>
        `;
        chatbotMessages.appendChild(userBubble);
        scrollToBottom();

        // Append typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'chatbot-typing';
        typingIndicator.className = 'flex gap-2 items-center text-slate-400 text-[11px] py-1';
        typingIndicator.innerHTML = `
            <div class="w-6 h-6 rounded bg-slate-900 text-white flex-shrink-0 flex items-center justify-center font-bold text-[10px]">RT</div>
            <div class="bg-white border border-slate-200 text-slate-500 px-3 py-1.5 rounded-lg flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style="animation-delay: 0.15s"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style="animation-delay: 0.3s"></span>
                <span class="ml-1 text-[10px]">Thinking...</span>
            </div>
        `;
        chatbotMessages.appendChild(typingIndicator);
        scrollToBottom();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText, page_context: window.location.pathname })
            });

            const data = await response.json();
            const typingEl = document.getElementById('chatbot-typing');
            if (typingEl) typingEl.remove();

            if (data.status === 'success') {
                const botBubble = document.createElement('div');
                botBubble.className = 'flex gap-2 items-start';
                botBubble.innerHTML = `
                    <div class="w-6 h-6 rounded bg-slate-900 text-white flex-shrink-0 flex items-center justify-center font-bold text-[10px]">
                        RT
                    </div>
                    <div class="bg-white border border-slate-200 text-slate-800 p-2.5 rounded-lg shadow-2xs max-w-[85%]">
                        <div class="text-[11.5px] leading-relaxed text-slate-700">
                            ${formatMarkdown(data.reply)}
                        </div>
                        ${data.disclaimer ? `
                        <div class="mt-2 pt-1.5 border-t border-slate-100 text-[9.5px] text-slate-400 italic">
                            ${data.disclaimer}
                        </div>` : ''}
                    </div>
                `;
                chatbotMessages.appendChild(botBubble);
            } else {
                throw new Error(data.error || 'Unable to process query');
            }
        } catch (err) {
            const typingEl = document.getElementById('chatbot-typing');
            if (typingEl) typingEl.remove();

            const errorBubble = document.createElement('div');
            errorBubble.className = 'flex gap-2 items-start';
            errorBubble.innerHTML = `
                <div class="w-6 h-6 rounded bg-rose-700 text-white flex-shrink-0 flex items-center justify-center font-bold text-[10px]">!</div>
                <div class="bg-rose-50 border border-rose-200 text-rose-800 p-2.5 rounded-lg text-[11px] max-w-[85%]">
                    Sorry, I could not process your request at this time. Please try again or check the <a href="/learning" class="underline font-medium">Learning Hub</a>.
                </div>
            `;
            chatbotMessages.appendChild(errorBubble);
        }

        scrollToBottom();
    }
});
