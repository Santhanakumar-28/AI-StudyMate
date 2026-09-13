/**
 * AI StudyMate - Timed Mock Test Engine
 * Enforces 60-second per question countdown, auto-advance on expiry,
 * anti-exploitation lockouts, and automated test submission.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Load active test session from sessionStorage or initialize
  const testDataRaw = sessionStorage.getItem('active_test_session');
  if (!testDataRaw) {
    UI.showToast('No active test found. Redirecting to setup...', 'warning');
    setTimeout(() => { window.location.href = '/setup-test'; }, 1500);
    return;
  }

  const testSession = JSON.parse(testDataRaw);
  const questions = testSession.questions || [];
  const sessionId = testSession.session_id;
  const totalQuestions = questions.length;

  if (totalQuestions === 0) {
    UI.showToast('Empty question set. Returning to setup...', 'error');
    setTimeout(() => { window.location.href = '/setup-test'; }, 1500);
    return;
  }

  // State
  let currentIndex = 0;
  const userAnswers = {}; // { "1": 0, "2": 2, ... }
  const expiredQuestions = new Set(); // Question numbers whose 60s timer has expired
  let timerInterval = null;
  let remainingSeconds = 60;

  // DOM Elements
  const qNumDisplay = document.getElementById('q-number-display');
  const qTotalDisplay = document.getElementById('q-total-display');
  const progressBarFill = document.getElementById('test-progress-bar-fill');
  const timerBadge = document.getElementById('timer-display');
  const topicBadge = document.getElementById('question-topic-badge');
  const diffBadge = document.getElementById('question-diff-badge');
  const promptDisplay = document.getElementById('question-prompt');
  const optionsContainer = document.getElementById('options-container');
  const prevBtn = document.getElementById('prev-btn');
  const nextBtn = document.getElementById('next-btn');
  const submitBtn = document.getElementById('submit-btn');
  const navigatorGrid = document.getElementById('navigator-grid');

  // Confirmation Modal
  const submitModal = document.getElementById('submit-modal');
  const modalAnsweredCount = document.getElementById('modal-answered-count');
  const modalTotalCount = document.getElementById('modal-total-count');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');
  const modalConfirmBtn = document.getElementById('modal-confirm-btn');

  // Initialize UI
  qTotalDisplay.textContent = totalQuestions;
  buildNavigator();
  loadQuestion(currentIndex);

  function buildNavigator() {
    navigatorGrid.innerHTML = '';
    for (let i = 0; i < totalQuestions; i++) {
      const qNum = i + 1;
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'nav-chip';
      chip.id = `nav-chip-${qNum}`;
      chip.textContent = String(qNum).padStart(2, '0');

      chip.addEventListener('click', () => {
        // Prevent navigating to expired questions
        if (expiredQuestions.has(qNum)) {
          UI.showToast(`Question ${qNum} has expired and cannot be revisited.`, 'warning', 2500);
          return;
        }
        if (i !== currentIndex) {
          switchQuestion(i);
        }
      });

      navigatorGrid.appendChild(chip);
    }
  }

  function updateNavigatorStates() {
    for (let i = 0; i < totalQuestions; i++) {
      const qNum = i + 1;
      const chip = document.getElementById(`nav-chip-${qNum}`);
      if (!chip) continue;

      chip.className = 'nav-chip';
      if (i === currentIndex) {
        chip.classList.add('current');
      }

      if (userAnswers[String(qNum)] !== undefined && userAnswers[String(qNum)] !== null) {
        chip.classList.add('answered');
      }

      if (expiredQuestions.has(qNum)) {
        chip.classList.add('expired');
      }
    }
  }

  function startTimer() {
    clearInterval(timerInterval);
    remainingSeconds = 60;
    updateTimerUI();

    timerInterval = setInterval(() => {
      remainingSeconds--;
      updateTimerUI();

      if (remainingSeconds <= 0) {
        clearInterval(timerInterval);
        handleTimerExpiry();
      }
    }, 1000);
  }

  function updateTimerUI() {
    timerBadge.textContent = `⏱ ${UI.formatTime(remainingSeconds)}`;
    if (remainingSeconds <= 10) {
      timerBadge.classList.add('timer-warning');
    } else {
      timerBadge.classList.remove('timer-warning');
    }
  }

  function handleTimerExpiry() {
    const currentQNum = currentIndex + 1;
    expiredQuestions.add(currentQNum);
    UI.showToast(`Time expired for Question ${currentQNum}. Auto-advancing...`, 'info', 2000);

    // If final question timed out, auto-submit test immediately
    if (currentIndex === totalQuestions - 1) {
      submitTest(true);
    } else {
      // Find next unexpired question
      let nextIdx = currentIndex + 1;
      while (nextIdx < totalQuestions && expiredQuestions.has(nextIdx + 1)) {
        nextIdx++;
      }

      if (nextIdx < totalQuestions) {
        switchQuestion(nextIdx);
      } else {
        submitTest(true);
      }
    }
  }

  function loadQuestion(index) {
    currentIndex = index;
    const q = questions[index];
    const qNum = index + 1;

    qNumDisplay.textContent = qNum;
    progressBarFill.style.width = `${((qNum) / totalQuestions) * 100}%`;

    topicBadge.textContent = q.topic || 'General';
    diffBadge.textContent = q.difficulty || 'Medium';
    promptDisplay.textContent = q.question;

    // Build Options
    optionsContainer.innerHTML = '';
    const letters = ['A', 'B', 'C', 'D'];
    const currentSelected = userAnswers[String(qNum)];

    q.options.forEach((optText, optIdx) => {
      const optItem = document.createElement('div');
      optItem.className = 'option-item';
      if (currentSelected === optIdx) {
        optItem.classList.add('selected');
      }

      optItem.innerHTML = `
        <div class="option-letter">${letters[optIdx]}</div>
        <div class="option-text">${optText}</div>
      `;

      optItem.addEventListener('click', () => {
        // Record user selection
        userAnswers[String(qNum)] = optIdx;
        
        // Update selection UI
        document.querySelectorAll('.option-item').forEach(el => el.classList.remove('selected'));
        optItem.classList.add('selected');
        updateNavigatorStates();
      });

      optionsContainer.appendChild(optItem);
    });

    // Control buttons visibility
    prevBtn.disabled = (index === 0);
    
    // Disable prev if previous questions are expired
    let hasAvailablePrev = false;
    for (let p = 0; p < index; p++) {
      if (!expiredQuestions.has(p + 1)) {
        hasAvailablePrev = true;
        break;
      }
    }
    if (!hasAvailablePrev) {
      prevBtn.disabled = true;
    }

    if (index === totalQuestions - 1) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-flex';
    } else {
      nextBtn.style.display = 'inline-flex';
      submitBtn.style.display = 'none';
    }

    updateNavigatorStates();
    startTimer();
  }

  function switchQuestion(newIndex) {
    loadQuestion(newIndex);
  }

  // Navigation button handlers
  prevBtn.addEventListener('click', () => {
    // Find closest available previous question
    for (let p = currentIndex - 1; p >= 0; p--) {
      if (!expiredQuestions.has(p + 1)) {
        switchQuestion(p);
        return;
      }
    }
    UI.showToast('Previous questions have expired.', 'warning');
  });

  nextBtn.addEventListener('click', () => {
    if (currentIndex < totalQuestions - 1) {
      switchQuestion(currentIndex + 1);
    }
  });

  // Manual Submission Confirmation Modal
  submitBtn.addEventListener('click', () => {
    const answeredCount = Object.keys(userAnswers).filter(k => userAnswers[k] !== undefined && userAnswers[k] !== null).length;
    modalAnsweredCount.textContent = answeredCount;
    modalTotalCount.textContent = totalQuestions;
    submitModal.classList.add('active');
  });

  modalCancelBtn.addEventListener('click', () => {
    submitModal.classList.remove('active');
  });

  modalConfirmBtn.addEventListener('click', () => {
    submitModal.classList.remove('active');
    submitTest(false);
  });

  // Submit test to backend
  async function submitTest(autoSubmitted = false) {
    clearInterval(timerInterval);
    if (autoSubmitted) {
      UI.showToast('Test timer finished. Submitting answers...', 'info');
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Grading Test...';

    const payload = {
      session_id: sessionId,
      answers: userAnswers,
      client_test_data: testSession
    };

    try {
      const res = await fetch('/api/submit-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (data.success) {
        // Clear active test from session storage to prevent retries
        sessionStorage.removeItem('active_test_session');
        window.location.href = data.redirect_url;
      } else {
        UI.showToast(data.error || 'Failed to submit test.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Test';
      }
    } catch (err) {
      UI.showToast('Network error during submission.', 'error');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Test';
    }
  }
});
