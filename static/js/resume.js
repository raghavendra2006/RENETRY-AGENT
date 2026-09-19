// ReTurn Platform - Resume Hub Interactive Enhancer & Generator
document.addEventListener('DOMContentLoaded', () => {
    const tabAnalysis = document.getElementById('tab-analysis');
    const tabDraft = document.getElementById('tab-draft');
    const tabUpload = document.getElementById('tab-upload');

    const panelAnalysis = document.getElementById('panel-analysis');
    const panelDraft = document.getElementById('panel-draft');
    const panelUpload = document.getElementById('panel-upload');

    function switchTab(activeTab, activePanel) {
        [tabAnalysis, tabDraft, tabUpload].forEach(t => {
            if (t) {
                t.classList.remove('border-teal-600', 'text-teal-700', 'font-semibold');
                t.classList.add('border-transparent', 'text-slate-600');
            }
        });
        [panelAnalysis, panelDraft, panelUpload].forEach(p => {
            if (p) p.classList.add('hidden');
        });

        if (activeTab && activePanel) {
            activeTab.classList.add('border-teal-600', 'text-teal-700', 'font-semibold');
            activeTab.classList.remove('border-transparent', 'text-slate-600');
            activePanel.classList.remove('hidden');
        }
    }

    if (tabAnalysis && panelAnalysis) {
        tabAnalysis.addEventListener('click', () => switchTab(tabAnalysis, panelAnalysis));
    }
    if (tabDraft && panelDraft) {
        tabDraft.addEventListener('click', () => switchTab(tabDraft, panelDraft));
    }
    if (tabUpload && panelUpload) {
        tabUpload.addEventListener('click', () => switchTab(tabUpload, panelUpload));
    }

    // Generate Updated Resume Action Button
    const generateBtn = document.getElementById('generate-updated-btn');
    const generateSpinner = document.getElementById('generate-spinner');
    const generateBtnText = document.getElementById('generate-btn-text');
    const draftTextarea = document.getElementById('resume-draft-text');
    const customRoleInput = document.getElementById('custom-target-role');

    if (generateBtn && draftTextarea) {
        generateBtn.addEventListener('click', async () => {
            generateBtn.disabled = true;
            generateBtn.classList.add('opacity-75', 'cursor-not-allowed');
            if (generateSpinner) generateSpinner.classList.remove('hidden');
            if (generateBtnText) generateBtnText.textContent = 'Generating .DOCX Resume...';

            const targetRole = customRoleInput ? customRoleInput.value.trim() : '';
            const currentDraft = draftTextarea.value.trim();

            try {
                const response = await fetch('/api/resume/generate-updated', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        target_role: targetRole,
                        draft_text: currentDraft
                    })
                });

                const data = await response.json();
                if (response.ok && data.success) {
                    if (data.updated_text) {
                        draftTextarea.value = data.updated_text;
                    }
                    if (generateBtnText) generateBtnText.textContent = '✓ Updated Resume Ready!';
                    setTimeout(() => {
                        if (generateBtnText) generateBtnText.textContent = 'Generate Updated Resume';
                    }, 2500);

                    // Show success notification
                    if (window.showToast) {
                        window.showToast('Updated resume and downloadable .docx file generated successfully!', 'success');
                    }
                } else {
                    alert(data.error || 'Failed to generate updated resume. Please ensure a resume is uploaded.');
                    if (generateBtnText) generateBtnText.textContent = 'Generate Updated Resume';
                }
            } catch (err) {
                console.error(err);
                alert('An unexpected network error occurred while generating your updated resume.');
                if (generateBtnText) generateBtnText.textContent = 'Generate Updated Resume';
            } finally {
                generateBtn.disabled = false;
                generateBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                if (generateSpinner) generateSpinner.classList.add('hidden');
            }
        });
    }

    // Copy Draft Text Button
    const copyDraftBtn = document.getElementById('copy-draft-btn');
    if (copyDraftBtn && draftTextarea) {
        copyDraftBtn.addEventListener('click', () => {
            draftTextarea.select();
            navigator.clipboard.writeText(draftTextarea.value).then(() => {
                const originalText = copyDraftBtn.textContent;
                copyDraftBtn.textContent = '✓ Copied!';
                setTimeout(() => {
                    copyDraftBtn.textContent = originalText;
                }, 2000);
            });
        });
    }

    // Print Draft
    const printDraftBtn = document.getElementById('print-draft-btn');
    if (printDraftBtn) {
        printDraftBtn.addEventListener('click', () => {
            window.print();
        });
    }
});
