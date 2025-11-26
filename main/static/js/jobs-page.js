// Drag & drop + file select logic for job application form

document.addEventListener('DOMContentLoaded', function () {
  // Сбросить все vacancy-details и .open при загрузке
  document.querySelectorAll('.mxd-project-item__promo').forEach(function (block) {
    block.classList.remove('open');
    var det = block.querySelector('.vacancy-details');
    if (det) det.style.display = 'none';
    var btn = block.querySelector('.vacancy-toggle-btn');
    if (btn) {
      btn.classList.remove('open');
      var btnText = btn.querySelector('.btn-text');
      // if (btnText) btnText.textContent = '{% if LANGUAGE_CODE == 'ru' %}Подробнее{% elif LANGUAGE_CODE == 'en' %}Learn More{% else %}Batafsil{% endif %}';
    }
  });
  // Vacancy details toggle
  document.querySelectorAll('.vacancy-toggle-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var promo = btn.closest('.mxd-project-item__promo');
      var details = btn.nextElementSibling;
      if (!details || !promo) return;
      var isOpen = promo.classList.contains('open');
      var btnText = btn.querySelector('.btn-text');
      if (!isOpen) {
        promo.classList.add('open');
        btn.classList.add('open');
        details.style.display = 'block';
        if (btnText) btnText.textContent = btnText.dataset.closeText;
      } else {
        promo.classList.remove('open');
        btn.classList.remove('open');
        details.style.display = 'none';
        if (btnText) btnText.textContent = btnText.dataset.openText;
      }
    });
  });
  const dropArea = document.getElementById('resume-drop-area');
  const fileInput = document.getElementById('resume-upload');
  const uploadBtn = document.getElementById('resume-upload-btn');
  const fileSelected = document.getElementById('file-selected');
  const fileError = document.getElementById('file-error');
  const form = document.getElementById('job-application-form');
  const formSuccess = document.getElementById('form-success');

  if (!dropArea || !fileInput || !uploadBtn) return;

  // Drag & drop events
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.add('dragover');
    });
  });
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.remove('dragover');
    });
  });
  dropArea.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      handleFileChange();
    }
  });

  // Button click opens file dialog
  uploadBtn.addEventListener('click', function (e) {
    e.preventDefault();
    fileInput.click();
  });

  // File input change
  fileInput.addEventListener('change', handleFileChange);

  function handleFileChange() {
    fileError.textContent = '';
    fileSelected.textContent = '';
    const file = fileInput.files[0];
    if (!file) return;
    // Проверка размера и типа
    const allowed = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowed.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|jpg|jpeg|png)$/i)) {
      fileError.textContent = 'Недопустимый формат файла.';
      fileInput.value = '';
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      fileError.textContent = 'Файл слишком большой (максимум 10 МБ).';
      fileInput.value = '';
      return;
    }
    fileSelected.textContent = 'Выбран файл: ' + file.name;
  }

  // Submit logic - РЕАЛЬНАЯ ОТПРАВКА
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    fileError.textContent = '';
    formSuccess.style.display = 'none';

    const file = fileInput.files[0];
    const regionSelect = document.getElementById('region-select');
    const jobSelect = document.getElementById('job-select');

    // Валидация на фронте
    let errorMsg = '';
    if (!regionSelect.value) {
      errorMsg += 'Пожалуйста, выберите город/регион.\n';
    }
    if (!jobSelect.value) {
      errorMsg += 'Пожалуйста, выберите вакансию.\n';
    }
    if (!file) {
      errorMsg += 'Пожалуйста, выберите файл.';
    }

    if (errorMsg) {
      fileError.textContent = errorMsg.trim();
      return;
    }

    // Создаём FormData для отправки файла
    const formData = new FormData();
    formData.append('region', regionSelect.value);
    formData.append('vacancy', jobSelect.value);  // ← ВАЖНО: vacancy, не job!
    formData.append('resume', file);

    // Получаем CSRF токен
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Определяем текущий язык из URL или cookie
    const currentLang = document.documentElement.lang || 'uz';
    const apiUrl = `/api/${currentLang}/job-applications/`;  // ← Используем роутер с языком

    // Блокируем кнопку отправки
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = currentLang === 'ru' ? 'Отправка...' : currentLang === 'en' ? 'Sending...' : 'Yuborilmoqda...';

    // AJAX запрос
    fetch(apiUrl, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      },
      body: formData
    })
      .then(response => {
        if (!response.ok) {
          return response.json().then(err => {
            throw new Error(JSON.stringify(err));
          });
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // Успех
          const successMessages = {
            'uz': 'Rezyume muvaffaqiyatli yuborildi!',
            'ru': 'Резюме успешно отправлено!',
            'en': 'Resume submitted successfully!'
          };

          formSuccess.textContent = data.message || successMessages[currentLang] || successMessages['uz'];
          formSuccess.style.display = 'block';
          formSuccess.style.color = 'green';

          // Сброс формы
          fileInput.value = '';
          fileSelected.textContent = '';
          regionSelect.selectedIndex = 0;
          jobSelect.selectedIndex = 0;

          setTimeout(() => {
            formSuccess.style.display = 'none';
          }, 4000);
        } else {
          // Ошибка с сервера
          fileError.textContent = data.message || 'Произошла ошибка';
        }
      })
      .catch(error => {
        window.logJSError('Job application submission error: ' + error.message, {
          file: 'job-applications.js',
          vacancy: jobSelect.value,
          region: regionSelect.value
        });

        try {
          const errorData = JSON.parse(error.message);
          if (errorData.vacancy) {
            fileError.textContent = 'Выберите вакансию из списка';
          } else if (errorData.resume) {
            fileError.textContent = 'Прикрепите файл резюме';
          } else if (errorData.region) {
            fileError.textContent = 'Выберите регион';
          } else {
            fileError.textContent = 'Ошибка: ' + JSON.stringify(errorData);
          }
        } catch {
          fileError.textContent = 'Ошибка соединения с сервером';
        }
      })
        .finally(() => {
      // Разблокируем кнопку
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    });
  });
});