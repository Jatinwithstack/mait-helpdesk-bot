function switchTab(tab) {
  const sectionFaqs = document.getElementById('sectionFaqs');
  const sectionUnanswered = document.getElementById('sectionUnanswered');
  const tabFaqBtn = document.getElementById('tabFaqBtn');
  const tabUnansweredBtn = document.getElementById('tabUnansweredBtn');

  if (tab === 'faqs') {
    sectionFaqs.style.display = 'block';
    sectionUnanswered.style.display = 'none';
    tabFaqBtn.classList.add('active');
    tabUnansweredBtn.classList.remove('active');
  } else {
    sectionFaqs.style.display = 'none';
    sectionUnanswered.style.display = 'block';
    tabFaqBtn.classList.remove('active');
    tabUnansweredBtn.classList.add('active');
  }
}

function openAddFaqModal() {
  document.getElementById('addFaqModal').classList.add('active');
}

function openEditFaqModal(id, category, question, answer) {
  const form = document.getElementById('editFaqForm');
  form.action = `/admin/faq/edit/${id}`;
  document.getElementById('editCategory').value = category;
  document.getElementById('editQuestion').value = question;
  document.getElementById('editAnswer').value = answer;
  document.getElementById('editFaqModal').classList.add('active');
}

function openConvertModal(id, category, question) {
  const form = document.getElementById('convertForm');
  form.action = `/admin/unanswered/convert/${id}`;
  document.getElementById('convertCategory').value = category;
  document.getElementById('convertQuestion').value = question;
  document.getElementById('convertAnswer').value = '';
  document.getElementById('convertModal').classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

// Close on clicking outside modal card
window.addEventListener('click', function(event) {
  ['addFaqModal', 'editFaqModal', 'convertModal'].forEach(id => {
    const el = document.getElementById(id);
    if (el && event.target === el) {
      el.classList.remove('active');
    }
  });
});
