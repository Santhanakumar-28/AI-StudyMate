/**
 * AI StudyMate - Result & Study Dashboard
 * Renders circular score animation, topic mastery breakdown,
 * and an interactive study-first error analysis interface.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const testId = window.TEST_ID;
  if (!testId) return;

  const loadingEl = document.getElementById('result-loading');
  const contentEl = document.getElementById('result-content');

  try {
    const res = await fetch(`/api/result/${testId}`);
    const data = await res.json();

    if (!data.success || !data.result) {
      loadingEl.innerHTML = `<div class="card text-center" style="padding: 3rem;"><p class="text-muted">Test result not found.</p><a href="/" class="btn btn-primary" style="margin-top: 1rem;">Return Home</a></div>`;
      return;
    }

    renderDashboard(data.result);
    loadingEl.style.display = 'none';
    contentEl.style.display = 'block';

  } catch (err) {
    loadingEl.innerHTML = `<div class="card text-center"><p class="text-muted">Error loading results.</p></div>`;
  }

  function renderDashboard(result) {
    // 1. Score percentage & radial animation
    const scorePct = result.score_percentage || 0;
    const scoreNumberEl = document.getElementById('score-number');
    const scoreProgressCircle = document.getElementById('score-radial-progress');
    const tierTitleEl = document.getElementById('tier-title');
    const tierMsgEl = document.getElementById('tier-message');

    scoreNumberEl.textContent = `${scorePct}%`;
    tierTitleEl.textContent = result.tier_title || 'Test Completed';
    tierMsgEl.textContent = result.tier_message || '';

    // Animate radial circle (circumference = 2 * PI * 70 ≈ 440)
    const offset = 440 - (440 * scorePct) / 100;
    setTimeout(() => {
      scoreProgressCircle.style.strokeDashoffset = offset;
    }, 150);

    // 2. Summary stats
    document.getElementById('stat-total').textContent = result.total_questions;
    document.getElementById('stat-correct').textContent = result.correct_count;
    document.getElementById('stat-wrong').textContent = result.wrong_count;
    document.getElementById('stat-unanswered').textContent = result.unanswered_count;

    // 3. Topic Mastery Breakdown
    const topicsContainer = document.getElementById('topic-breakdown-container');
    topicsContainer.innerHTML = '';

    (result.topic_breakdown || []).forEach(tb => {
      const row = document.createElement('div');
      row.className = 'topic-row';
      row.innerHTML = `
        <div class="topic-label-bar">
          <span>${tb.topic}</span>
          <span><strong>${tb.percentage}%</strong> (${tb.correct}/${tb.total})</span>
        </div>
        <div class="topic-bar-bg">
          <div class="topic-bar-fill" style="width: ${tb.percentage}%"></div>
        </div>
      `;
      topicsContainer.appendChild(row);
    });

    // 4. Review & Study Cards with Filters
    const filterPills = document.querySelectorAll('.filter-pill');
    const reviewCardsContainer = document.getElementById('review-cards-container');
    const cardsData = result.review_cards || [];

    // Update filter counts
    document.getElementById('count-all').textContent = cardsData.length;
    document.getElementById('count-wrong').textContent = result.wrong_count;
    document.getElementById('count-correct').textContent = result.correct_count;
    document.getElementById('count-unanswered').textContent = result.unanswered_count;

    function renderReviewCards(filter = 'all') {
      reviewCardsContainer.innerHTML = '';
      const filtered = cardsData.filter(card => {
        if (filter === 'all') return true;
        return card.status === filter;
      });

      if (filtered.length === 0) {
        reviewCardsContainer.innerHTML = `
          <div class="card text-center" style="padding: 2.5rem;">
            <p class="text-muted">No questions found in this filter category.</p>
          </div>
        `;
        return;
      }

      filtered.forEach(card => {
        const cardEl = document.createElement('div');
        cardEl.className = `review-card ${card.status}`;

        let statusBadge = '';
        let userBoxClass = '';
        if (card.status === 'correct') {
          statusBadge = `<span class="badge badge-success">✓ Correct</span>`;
          userBoxClass = 'user-correct';
        } else if (card.status === 'wrong') {
          statusBadge = `<span class="badge badge-error">❌ Incorrect</span>`;
          userBoxClass = 'user-wrong';
        } else {
          statusBadge = `<span class="badge badge-warning">○ Unanswered</span>`;
          userBoxClass = 'user-unanswered';
        }

        cardEl.innerHTML = `
          <div class="review-meta">
            <span class="badge badge-neutral">Question ${card.question_number}</span>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
              <span class="badge badge-primary">${card.topic}</span>
              <span class="badge badge-neutral">${card.difficulty}</span>
              ${statusBadge}
            </div>
          </div>
          
          <div class="review-question">${card.question}</div>

          <div class="answer-comparison-grid">
            <div class="answer-box ${userBoxClass}">
              <div class="answer-title">Your Answer</div>
              <div style="font-weight: 600;">${card.user_selected_text}</div>
            </div>
            
            <div class="answer-box correct-target">
              <div class="answer-title" style="color: var(--success-text);">Correct Answer</div>
              <div style="font-weight: 600; color: var(--success-text);">${card.correct_text}</div>
            </div>
          </div>

          <div class="explanation-box">
            <div style="font-weight: 700; color: var(--text-main); margin-bottom: 0.35rem;">💡 Explanation</div>
            <div>${card.explanation}</div>
          </div>

          ${card.source_reference ? `
            <div class="source-ref-badge">
              📄 Source Reference: <span>${card.source_reference}</span>
            </div>
          ` : ''}
        `;

        reviewCardsContainer.appendChild(cardEl);
      });
    }

    // Filter pill click listeners
    filterPills.forEach(pill => {
      pill.addEventListener('click', () => {
        filterPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        const filterType = pill.getAttribute('data-filter');
        renderReviewCards(filterType);
      });
    });

    // Default view: render all
    renderReviewCards('all');
  }
});
