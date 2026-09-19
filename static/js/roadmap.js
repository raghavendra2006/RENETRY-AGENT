// ReTurn Platform - Roadmap Task Completion, Dynamic Stage Tests & AI Roadmap Generator Handler
document.addEventListener('DOMContentLoaded', () => {
    // 1. Task Checkbox Toggling
    const taskCheckboxes = document.querySelectorAll('.roadmap-task-checkbox');
    const progressBar = document.getElementById('roadmap-progress-bar');
    const progressText = document.getElementById('roadmap-progress-text');
    const completedCountText = document.getElementById('roadmap-completed-count');

    taskCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async () => {
            const taskId = checkbox.dataset.taskId;
            const taskLabel = document.getElementById(`task-label-${taskId}`);

            try {
                const response = await fetch('/api/roadmap/task/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId })
                });

                const data = await response.json();
                if (data.success) {
                    if (taskLabel) {
                        if (data.is_completed) {
                            taskLabel.classList.add('line-through', 'text-slate-400');
                        } else {
                            taskLabel.classList.remove('line-through', 'text-slate-400');
                        }
                    }

                    if (progressBar) {
                        progressBar.style.width = `${data.percentage}%`;
                    }
                    if (progressText) {
                        progressText.textContent = `${data.percentage}%`;
                    }
                    if (completedCountText && data.completed_tasks !== undefined) {
                        completedCountText.textContent = data.completed_tasks;
                    }
                } else {
                    checkbox.checked = !checkbox.checked;
                    alert(data.error || 'Failed to update task status.');
                }
            } catch (err) {
                console.error('Roadmap error:', err);
                checkbox.checked = !checkbox.checked;
            }
        });
    });

    // 2. Stage Evaluation Test Modal & Flow
    const testModal = document.getElementById('stage-test-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelTestBtn = document.getElementById('cancel-test-btn');
    const modalStageTitle = document.getElementById('modal-stage-title');
    const modalLoading = document.getElementById('modal-loading');
    const testForm = document.getElementById('stage-test-form');
    const questionsList = document.getElementById('questions-list');
    const testResultsView = document.getElementById('test-results-view');
    const submitTestBtn = document.getElementById('submit-test-btn');

    let currentTestStageNum = null;

    function openModal() {
        if (testModal) testModal.classList.remove('hidden');
    }

    function closeModal() {
        if (testModal) testModal.classList.add('hidden');
        if (testResultsView) testResultsView.classList.add('hidden');
        if (testForm) {
            testForm.reset();
            testForm.classList.add('hidden');
        }
    }

    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if (cancelTestBtn) cancelTestBtn.addEventListener('click', closeModal);

    // Attach click listeners to all "Take Stage Test" buttons
    const takeTestButtons = document.querySelectorAll('.take-stage-test-btn');
    takeTestButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const stageNum = parseInt(btn.dataset.stageNum, 10);
            const stageTitle = btn.dataset.stageTitle || `Stage ${stageNum}`;
            currentTestStageNum = stageNum;

            if (modalStageTitle) {
                modalStageTitle.textContent = `Stage ${stageNum}: ${stageTitle}`;
            }

            openModal();
            if (modalLoading) modalLoading.classList.remove('hidden');
            if (testForm) testForm.classList.add('hidden');
            if (testResultsView) testResultsView.classList.add('hidden');

            try {
                const response = await fetch(`/api/roadmap/stage-test/${stageNum}`);
                const data = await response.json();

                if (modalLoading) modalLoading.classList.add('hidden');

                if (data.success && data.questions && data.questions.length > 0) {
                    renderTestQuestions(data.questions);
                    if (testForm) testForm.classList.remove('hidden');
                } else {
                    alert(data.error || 'Could not load stage test questions. Please try again.');
                    closeModal();
                }
            } catch (err) {
                console.error(err);
                if (modalLoading) modalLoading.classList.add('hidden');
                alert('Network error loading test questions.');
                closeModal();
            }
        });
    });

    function renderTestQuestions(questions) {
        if (!questionsList) return;
        let html = '';

        questions.forEach((q, idx) => {
            const optionsHtml = q.options.map((opt, optIdx) => `
                <label class="flex items-start gap-2.5 p-3 rounded-lg border border-slate-200 hover:border-teal-400 hover:bg-slate-50 cursor-pointer transition text-xs text-slate-800">
                    <input type="radio" name="q_${q.id}" value="${optIdx}" required class="mt-0.5 text-teal-600 focus:ring-teal-500">
                    <span class="leading-relaxed">${esc(opt)}</span>
                </label>
            `).join('');

            html += `
                <div class="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-slate-900 text-xs">Question ${idx + 1} of ${questions.length}</span>
                        <span class="text-[10px] font-semibold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200 uppercase">${esc(q.topic_tag)}</span>
                    </div>
                    <p class="text-xs font-semibold text-slate-800 leading-relaxed">${esc(q.question)}</p>
                    <div class="space-y-2 pt-1">
                        ${optionsHtml}
                    </div>
                </div>
            `;
        });

        questionsList.innerHTML = html;
    }

    // Submit Evaluation Handler
    if (testForm) {
        testForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!currentTestStageNum) return;

            // Collect answers
            const formData = new FormData(testForm);
            const answers = {};
            for (let [key, val] of formData.entries()) {
                if (key.startsWith('q_')) {
                    const qId = key.substring(2);
                    answers[qId] = parseInt(val, 10);
                }
            }

            submitTestBtn.disabled = true;
            submitTestBtn.innerHTML = '<svg class="w-4 h-4 animate-spin inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Evaluating Answers...';

            try {
                const response = await fetch('/api/roadmap/evaluate-stage', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stage_number: currentTestStageNum,
                        answers: answers
                    })
                });

                const data = await response.json();
                if (data.success) {
                    testForm.classList.add('hidden');
                    renderEvaluationResults(data);
                    if (testResultsView) testResultsView.classList.remove('hidden');

                    // If passed, trigger toast notification
                    if (data.passed) {
                        if (window.showToast) {
                            window.showToast(`Congratulations! Stage ${currentTestStageNum} passed with ${data.score}%!`, 'success');
                        }
                    }
                } else {
                    alert(data.error || 'Evaluation failed.');
                }
            } catch (err) {
                console.error(err);
                alert('An error occurred while evaluating your test.');
            } finally {
                submitTestBtn.disabled = false;
                submitTestBtn.innerHTML = '<span>Submit Stage Evaluation</span> &rarr;';
            }
        });
    }

    function renderEvaluationResults(report) {
        if (!testResultsView) return;

        const isPassed = report.passed;
        const bannerBg = isPassed ? 'bg-emerald-50 border-emerald-300 text-emerald-950' : 'bg-amber-50 border-amber-300 text-amber-950';
        const badgeBg = isPassed ? 'bg-emerald-600 text-white' : 'bg-amber-600 text-white';
        const statusText = isPassed ? 'PASSED & ADVANCED' : 'REVISION NEEDED';

        let weakTopicsHtml = '';
        if (report.weak_topics && report.weak_topics.length > 0) {
            weakTopicsHtml = `
                <div class="p-3 bg-amber-50 border border-amber-200 rounded text-xs space-y-1.5">
                    <strong class="text-amber-900 font-bold">Topics Requiring Revision Before Retake:</strong>
                    <ul class="list-disc pl-4 space-y-0.5 text-amber-800 text-[11px]">
                        ${report.weak_topics.map(wt => `<li>${esc(wt)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        let reviewListHtml = '';
        if (report.explanation_summary && Array.isArray(report.explanation_summary)) {
            reviewListHtml = report.explanation_summary.map((item, idx) => `
                <div class="p-3.5 bg-white border border-slate-200 rounded-lg text-xs space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-slate-900">Question ${idx + 1}</span>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase ${item.is_correct ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}">
                            ${item.is_correct ? '✓ Correct' : '✗ Incorrect'}
                        </span>
                    </div>
                    <p class="font-medium text-slate-800">${esc(item.question)}</p>
                    <div class="space-y-1 text-[11px] pt-1">
                        <div class="text-slate-600"><span class="font-semibold text-slate-700">Your Answer:</span> ${esc(item.user_choice)}</div>
                        ${!item.is_correct ? `<div class="text-emerald-800 font-semibold"><span class="text-emerald-700">Correct Answer:</span> ${esc(item.correct_choice)}</div>` : ''}
                        <div class="p-2 bg-slate-50 border border-slate-200 rounded text-slate-600 mt-1 leading-relaxed"><strong class="text-slate-700">Explanation:</strong> ${esc(item.explanation)}</div>
                    </div>
                </div>
            `).join('');
        }

        testResultsView.innerHTML = `
            <!-- Score Banner -->
            <div class="p-5 border rounded-xl ${bannerBg} space-y-2">
                <div class="flex items-center justify-between">
                    <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${badgeBg}">${statusText}</span>
                    <span class="text-2xl font-black ${isPassed ? 'text-emerald-700' : 'text-amber-700'}">${report.score}%</span>
                </div>
                <div class="text-xs">
                    You answered <strong>${report.correct_answers}</strong> of <strong>${report.total_questions}</strong> questions correctly. Passing threshold is <strong>${report.passing_score}%</strong>.
                </div>
                ${isPassed ? '<p class="text-xs font-semibold text-emerald-800">✓ Next stage has been unlocked! Your roadmap progression has been updated.</p>' : '<p class="text-xs text-amber-800">Review the explanations below and recommended topics, then retake the evaluation when ready.</p>'}
            </div>

            ${weakTopicsHtml}

            <!-- Detailed Question Review -->
            <div class="space-y-3">
                <h4 class="font-bold text-slate-900 text-xs uppercase tracking-wider">Question-by-Question Review & Explanations</h4>
                <div class="space-y-3">
                    ${reviewListHtml}
                </div>
            </div>

            <div class="pt-4 border-t border-slate-200 flex items-center justify-between">
                <button type="button" onclick="window.location.reload()" class="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded transition flex items-center gap-1.5 cursor-pointer">
                    <span>Done & Refresh Roadmap</span> &rarr;
                </button>
            </div>
        `;
    }

    // 3. AI-Personalized Roadmap Generation Handler
    const aiBtn = document.getElementById('generate-ai-roadmap-btn');
    const aiLoading = document.getElementById('ai-roadmap-loading');
    const aiContent = document.getElementById('ai-roadmap-content');
    const aiEmpty = document.getElementById('ai-roadmap-empty');

    if (aiBtn) {
        aiBtn.addEventListener('click', async () => {
            aiBtn.disabled = true;
            aiBtn.innerHTML = '<svg class="w-4 h-4 animate-spin inline" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Generating...';
            if (aiLoading) aiLoading.classList.remove('hidden');
            if (aiContent) aiContent.classList.add('hidden');
            if (aiEmpty) aiEmpty.classList.add('hidden');

            try {
                const resp = await fetch('/api/ai/generate-roadmap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await resp.json();
                if (aiLoading) aiLoading.classList.add('hidden');

                if (data.success && data.roadmap) {
                    renderAIRoadmap(data.roadmap);
                    if (aiContent) aiContent.classList.remove('hidden');
                    if (window.showToast) window.showToast('AI Roadmap generated successfully!', 'success');
                } else {
                    if (aiEmpty) aiEmpty.classList.remove('hidden');
                    if (window.showToast) window.showToast(data.error || 'Could not generate roadmap', 'error');
                }
            } catch (err) {
                if (aiLoading) aiLoading.classList.add('hidden');
                if (aiEmpty) aiEmpty.classList.remove('hidden');
                if (window.showToast) window.showToast('Failed to generate AI roadmap', 'error');
            }

            aiBtn.disabled = false;
            aiBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Generate AI Roadmap';
        });
    }

    function renderAIRoadmap(roadmap) {
        if (!aiContent) return;
        const phaseColors = [
            { bg: 'bg-teal-50', border: 'border-teal-200', badge: 'bg-teal-600', text: 'text-teal-900' },
            { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-600', text: 'text-blue-900' },
            { bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-600', text: 'text-purple-900' },
            { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-600', text: 'text-emerald-900' }
        ];

        let html = '';

        if (roadmap.target_summary) {
            html += `
                <div class="p-4 bg-gradient-to-r from-teal-900 via-slate-900 to-indigo-950 text-white rounded-lg shadow-sm">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded bg-teal-400 text-teal-950">AI Generated</span>
                        <span class="text-xs text-teal-200">${esc(roadmap.estimated_duration || '10-12 weeks')}</span>
                    </div>
                    <p class="text-sm font-medium text-slate-100">${esc(roadmap.target_summary)}</p>
                </div>
            `;
        }

        if (roadmap.phases && Array.isArray(roadmap.phases)) {
            roadmap.phases.forEach((phase, idx) => {
                const c = phaseColors[idx % phaseColors.length];
                const skillsHtml = (phase.skills || []).map(s => `
                    <div class="p-2 bg-white rounded border border-slate-200 text-xs">
                        <div class="font-semibold text-slate-900">${esc(s.name)}</div>
                        <div class="text-slate-500 text-[11px] mt-0.5">${esc(s.why || '')}</div>
                        ${s.resource_suggestion ? '<div class="text-teal-700 text-[11px] mt-0.5 font-medium">📚 ' + esc(s.resource_suggestion) + '</div>' : ''}
                    </div>
                `).join('');

                const activitiesHtml = (phase.practice_activities || []).map(a => `
                    <li class="flex items-start gap-1.5"><span class="text-teal-600 mt-0.5">▸</span> ${esc(a)}</li>
                `).join('');

                html += `
                    <div class="${c.bg} ${c.border} border rounded-lg overflow-hidden">
                        <div class="p-4 border-b ${c.border} flex items-center justify-between">
                            <div class="flex items-center gap-3">
                                <span class="w-8 h-8 rounded-full ${c.badge} text-white font-bold text-xs flex items-center justify-center">${phase.phase_number || idx + 1}</span>
                                <div>
                                    <h3 class="text-sm font-bold ${c.text}">${esc(phase.title)}</h3>
                                    <span class="text-[11px] text-slate-500">${esc(phase.duration || '')}</span>
                                </div>
                            </div>
                        </div>
                        <div class="p-4 space-y-3">
                            <p class="text-xs text-slate-700 font-medium">${esc(phase.objective || '')}</p>
                            ${skillsHtml ? '<div class="grid grid-cols-1 sm:grid-cols-2 gap-2">' + skillsHtml + '</div>' : ''}
                            ${activitiesHtml ? '<div class="mt-2"><div class="text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">Practice Activities</div><ul class="space-y-1 text-xs text-slate-700">' + activitiesHtml + '</ul></div>' : ''}
                            ${phase.expected_outcome ? '<div class="mt-2 p-2 bg-white/60 rounded text-[11px] text-slate-600"><strong class="text-slate-800">Expected Outcome:</strong> ' + esc(phase.expected_outcome) + '</div>' : ''}
                        </div>
                    </div>
                `;
            });
        }

        aiContent.innerHTML = html;
    }

    function esc(str) {
        if (!str) return '';
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }
});

