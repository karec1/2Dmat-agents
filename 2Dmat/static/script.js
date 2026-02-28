// static/script.js
// Основные JavaScript функции для веб-интерфейса

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Обработчик для экспорта данных
    document.querySelectorAll('.export-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const format = this.dataset.format;
            exportData(format);
        });
    });
    
    // Динамическое обновление значения ползунка Tc
    const tcSlider = document.querySelector('input[name="min_tc"]');
    if (tcSlider) {
        tcSlider.addEventListener('input', function() {
            document.getElementById('tcValue').textContent = this.value + ' K';
        });
    }
    
    // Быстрый поиск по таблице
    const searchInput = document.getElementById('tableSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#materialsTable tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
});

// Функция экспорта данных
function exportData(format) {
    let url;
    
    switch(format) {
        case 'csv':
            url = '/export/csv';
            break;
        case 'json':
            // If you add JSON export later
            alert('JSON экспорт пока не реализован');
            return;
        default:
            alert('Формат не поддерживается');
            return;
    }
    
    // Add current filter parameters
    const params = new URLSearchParams(window.location.search);
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    window.location.href = url;
}

// Копирование ссылки API
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('Скопировано в буфер обмена!');
    }).catch(err => {
        console.error('Ошибка копирования: ', err);
    });
}

// Отображение предупреждения о загрузке
function showLoading(message = 'Загрузка...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loading';
    loadingDiv.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    `;
    loadingDiv.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">${message}</span>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// Валидация химических формул
function isValidFormula(formula) {
    // Простая проверка: формула должна содержать хотя бы одну букву и одну цифру
    const regex = /^[A-Z][a-z]?\d*([A-Z][a-z]?\d*)*$/;
    return regex.test(formula);
}

// API вызовы
async function fetchMaterialStats() {
    try {
        const response = await fetch('/api/stats');
        return await response.json();
    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
        return null;
    }
}

// Отображение статистики на странице
async function displayStats() {
    const stats = await fetchMaterialStats();
    if (stats) {
        // Обновление элементов DOM со статистикой
        document.querySelectorAll('.stats-total').forEach(el => {
            el.textContent = stats.total_materials;
        });
    }
}

// Инициализация при загрузке страницы
window.addEventListener('load', () => {
    // displayStats(); // Раскомментировать, если нужна динамическая статистика
    
    // Автоматическое форматирование химических формул
    document.querySelectorAll('.chemical-formula').forEach(el => {
        const formula = el.textContent;
        // Простое форматирование: подстрочные цифры
        const formatted = formula.replace(/(\d+)/g, '<sub>$1</sub>');
        el.innerHTML = formatted;
    });
});