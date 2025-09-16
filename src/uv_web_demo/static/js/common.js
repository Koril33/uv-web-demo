const defaultFontSize = 16;
const defaultLineHeight = 1.8;
const defaultLetterSpacing = 2;
const defaultFontFamily = "Georgia, serif";

const content = document.getElementById('content');
// 从页面传递的数据中读取
const bookId = window.chapterData?.bookId;
const chapterId = window.chapterData?.chapterId;

if (!bookId || !chapterId) {
    console.warn("未提供 chapter 数据，跳过滚动位置功能");
}
// 从 localStorage 读取保存的设置，或使用默认值
let fontSize = parseFloat(localStorage.getItem('fontSize')) || defaultFontSize;
let lineHeight = parseFloat(localStorage.getItem('lineHeight')) || defaultLineHeight;
let fontFamily = localStorage.getItem('fontFamily') || defaultFontFamily;
let letterSpacing = parseFloat(localStorage.getItem('letterSpacing')) || defaultLetterSpacing;

// 页面加载时恢复样式
function restoreStyles() {
    if (!content) return;

    content.style.fontSize = fontSize + 'px';
    content.style.lineHeight = lineHeight;
    content.style.fontFamily = fontFamily;
    content.style.letterSpacing = letterSpacing + 'px';
}

// 调整字体大小
function adjustFont(delta) {
    if (!content) return;
    fontSize = Math.min(Math.max(12, fontSize + delta), 30);
    content.style.fontSize = fontSize + 'px';
    localStorage.setItem('fontSize', fontSize);
}

// 调整行间距
function adjustLine(delta) {
    if (!content) return;
    lineHeight = Math.min(Math.max(1.2, lineHeight + delta), 5);
    content.style.lineHeight = lineHeight;
    localStorage.setItem('lineHeight', lineHeight);
}

function adjustLetterSpacing(delta) {
    if (!content) return;
    letterSpacing = Math.min(Math.max(1, letterSpacing + delta), 10);
    content.style.letterSpacing = letterSpacing + 'px';
    localStorage.setItem('letterSpacing', letterSpacing);
}

// 切换字体
function changeFontFamily(fontFamily) {
    if (!content) return;
    content.style.fontFamily = fontFamily;
    localStorage.setItem('fontFamily', fontFamily);
}

// 重置样式并保存默认值
function resetStyle() {
    if (!content) return;
    fontSize = defaultFontSize;
    lineHeight = defaultLineHeight;
    fontFamily = defaultFontFamily;
    letterSpacing = defaultLetterSpacing;

    content.style.fontSize = fontSize + 'px';
    content.style.lineHeight = lineHeight;
    content.style.fontFamily = fontFamily;
    content.style.letterSpacing = letterSpacing + 'px';

    localStorage.setItem('fontSize', fontSize);
    localStorage.setItem('lineHeight', lineHeight);
    localStorage.setItem('fontFamily', fontFamily);
    localStorage.setItem('letterSpacing', letterSpacing);
}

// 切换暗黑模式
function toggleDark() {
    document.body.classList.toggle('dark');
    localStorage.setItem('darkMode', document.body.classList.contains('dark'));
}


// 导航相关函数（保持不变）
function updateNavRightPosition() {
    const navLeft = document.querySelector('.nav-left');
    const navRight = document.querySelector('.nav-right');

    if (!navLeft || !navRight) return;

    const height = navLeft.offsetHeight;
    navRight.style.top = `calc(100% + ${height}px)`;
}


function toggleNav() {
    document.body.classList.toggle('nav-open');
    setTimeout(updateNavRightPosition, 10);
}

// 防抖函数：避免频繁保存
function debounce(func, delay) {
    let timer;
    return function () {
        const context = this;
        const args = arguments;
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(context, args), delay);
    };
}

// 保存滚动位置（按 book_id + chapter_id）
function saveScrollPosition() {
    if (!bookId || !chapterId) return;
    const key = `scrollPos_${bookId}_${chapterId}`;
    localStorage.setItem(key, window.scrollY.toString());
}

// 防抖版本，每 500ms 最多保存一次
const debouncedSaveScroll = debounce(saveScrollPosition, 500);

// 恢复滚动位置
function restoreScrollPosition() {
    if (!bookId || !chapterId) return;
    const key = `scrollPos_${bookId}_${chapterId}`;
    const savedPos = localStorage.getItem(key);
    if (savedPos === null) return;

    const targetPos = parseFloat(savedPos);

    // 等待页面完全加载，避免因图片加载导致滚动错位
    if (document.readyState === 'complete') {
        window.scrollTo({
            top: targetPos,
            left: 0,
            behavior: 'smooth'
        });
    } else {
        window.addEventListener('load', () => {
            window.scrollTo({
                top: targetPos,
                left: 0,
                behavior: 'smooth'
            });
        });
    }
}

// 清除当前章节的滚动位置记录
function clearCurrentScroll() {
    if (!bookId || !chapterId) {
        console.warn("无法清除滚动位置：缺少 bookId 或 chapterId");
        return;
    }

    const key = `scrollPos_${bookId}_${chapterId}`;
    localStorage.removeItem(key);
    console.log("已清除滚动位置:", key);
}

// 更新阅读进度
function updateReadingProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.body.scrollHeight;
    const winHeight = window.innerHeight;

    // 可滚动的总高度
    const scrollableHeight = docHeight - winHeight;

    let progress = 0;
    if (scrollableHeight <= 0) {
        progress = 100;
    } else {
        progress = (scrollTop / scrollableHeight) * 100;
        progress = Math.min(100, Math.max(0, progress)); // 限制在 0-100
    }

    const progressElement = document.getElementById('readingProgress');
    if (progressElement) {
        progressElement.textContent = `${Math.round(progress)}%`;
    }
}

// 切换目录下拉菜单
function toggleChapterDropdown() {
    const dropdownMenu = document.querySelector('.chapter-dropdown .dropdown-menu');
    if (dropdownMenu) {
        dropdownMenu.style.display = dropdownMenu.style.display === 'block' ? 'none' : 'block';
    }
}

function closeChapterDropdown(e) {
    const dropdown = document.querySelector('.chapter-dropdown');
    const menu = document.querySelector('.dropdown-menu');

    if (!dropdown.contains(e.target)) {
        if (menu) menu.style.display = 'none';
    }
}


window.addEventListener('load', updateNavRightPosition);
window.addEventListener('resize', updateNavRightPosition);
window.addEventListener('scroll', debouncedSaveScroll);
window.addEventListener('scroll', updateReadingProgress);
document.addEventListener('click', closeChapterDropdown);
// 页面加载完成后恢复所有用户偏好
document.addEventListener('DOMContentLoaded', () => {
    // 恢复暗黑模式
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark');
    }

    // 恢复字体选择下拉框
    const fontSelect = document.querySelector('.controls select');
    if (fontSelect) {
        fontSelect.value = fontFamily; // 设置为当前字体
    }

    // 恢复字体和行高
    restoreStyles();

    // 初始化导航位置（如果 content 还没加载完，稍后也会在 load 时更新）
    updateNavRightPosition();

    restoreScrollPosition();

    setTimeout(updateReadingProgress, 100); // 稍等一下确保渲染完成

    const toggle = document.querySelector('.dropdown-toggle');
    if (toggle) {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation(); // 阻止立即关闭
            toggleChapterDropdown();
        });
    }
});