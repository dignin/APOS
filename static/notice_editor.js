const editor = document.getElementById('notice-editor');
const form = document.getElementById('notice-form');
const source = document.getElementById('markdown-source');
const workspace = document.getElementById('markdown-workspace');
const preview = document.getElementById('markdown-preview');
const status = document.getElementById('preview-status');
const toolbar = document.querySelector('.editor-toolbar');
const visualButton = document.getElementById('visual-mode');
const markdownButton = document.getElementById('markdown-mode');
let mode = document.getElementById('notice-format').value;
let dirty = false;
let selectionRange;
let visualMarkdown = null;
let previewVersion = 0;
let previewTimer;
const isGerman = document.documentElement.lang === 'de';
async function renderMarkdown(text) {
    const body = new FormData();
    body.set('csrf', form.elements.csrf.value);
    body.set('content', text);
    const response = await fetch(editor.dataset.previewUrl, {method: 'POST', body, redirect: 'error'});
    if (!response.ok) throw new Error('Preview failed');
    return await response.text();
}
function updateMode() {
    editor.hidden = mode !== 'html';
    workspace.hidden = mode !== 'markdown';
    toolbar.hidden = mode !== 'html';
    visualButton.setAttribute('aria-pressed', String(mode === 'html'));
    markdownButton.setAttribute('aria-pressed', String(mode === 'markdown'));
}
function markdownText(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent.replace(/([\\`*_\[\]])/g, '\\$1');
    if (node.nodeType !== Node.ELEMENT_NODE) return '';
    const inner = Array.from(node.childNodes).map(markdownText).join('');
    const tag = node.tagName.toLowerCase();
    if (/^h[1-6]$/.test(tag)) return '\n\n' + '#'.repeat(Number(tag[1])) + ' ' + inner.trim() + '\n\n';
    if (tag === 'p' || tag === 'div') return '\n\n' + inner.trim() + '\n\n';
    if (tag === 'br') return '  \n';
    if (tag === 'hr') return '\n\n---\n\n';
    if (tag === 'strong' || tag === 'b') return '**' + inner + '**';
    if (tag === 'em' || tag === 'i') return '*' + inner + '*';
    if (tag === 's') return '~~' + inner + '~~';
    if (tag === 'a' && node.hasAttribute('href')) return '[' + inner + '](<' + node.getAttribute('href') + '>)';
    if (tag === 'pre') {
        const text = node.textContent;
        const runs = text.match(/`+/g) || [];
        const fence = '`'.repeat(Math.max(3, ...runs.map(run => run.length + 1)));
        return '\n\n' + fence + '\n' + text + '\n' + fence + '\n\n';
    }
    if (tag === 'code') {
        const text = node.textContent;
        const fence = '`'.repeat(Math.max(1, ...(text.match(/`+/g) || []).map(run => run.length + 1)));
        return fence + ' ' + text + ' ' + fence;
    }
    if (tag === 'blockquote') return '\n\n' + inner.trim().split('\n').map(line => '> ' + line).join('\n') + '\n\n';
    if (tag === 'ul' || tag === 'ol') {
        return '\n\n' + Array.from(node.children).map((child, index) => {
            const marker = tag === 'ol' ? (index + 1) + '. ' : '- ';
            return marker + markdownText(child).trim().replace(/\n/g, '\n    ');
        }).join('\n') + '\n\n';
    }
    if (tag === 'table') {
        const rows = Array.from(node.querySelectorAll('tr')).map(row => '| ' + Array.from(row.children).map(cell => markdownText(cell).trim().replace(/\|/g, '\\|').replace(/\n/g, ' ')).join(' | ') + ' |');
        if (rows.length) rows.splice(1, 0, '| ' + Array.from(node.querySelector('tr').children).map(() => '---').join(' | ') + ' |');
        return '\n\n' + rows.join('\n') + '\n\n';
    }
    return inner;
}
async function updatePreview() {
    const version = ++previewVersion;
    try {
        const html = await renderMarkdown(source.value);
        if (version !== previewVersion) return;
        preview.innerHTML = html;
        status.textContent = '';
    } catch (error) {
        if (version === previewVersion) status.textContent = isGerman ? 'Vorschau nicht verfügbar. Ihr Text bleibt erhalten.' : 'Preview unavailable. Your text is retained.';
    }
}
markdownButton.addEventListener('click', () => {
    if (mode === 'markdown') return;
    source.value = visualMarkdown !== null ? visualMarkdown : Array.from(editor.childNodes).map(markdownText).join('').trim();
    mode = 'markdown'; updateMode(); updatePreview(); source.focus();
});
visualButton.addEventListener('click', async () => {
    if (mode === 'html') return;
    visualButton.disabled = true;
    const value = source.value;
    try {
        const html = await renderMarkdown(value);
        if (source.value !== value) return;
        editor.innerHTML = html;
        visualMarkdown = value;
        selectionRange = null; mode = 'html'; updateMode(); editor.focus();
    } catch (error) {
        status.textContent = isGerman ? 'Vorschau nicht verfügbar. Markdown bleibt erhalten.' : 'Preview unavailable. Markdown is retained.';
    } finally { visualButton.disabled = false; }
});
function rememberSelection() {
    const selection = window.getSelection();
    if (selection.rangeCount && editor.contains(selection.anchorNode)) selectionRange = selection.getRangeAt(0).cloneRange();
}
document.addEventListener('selectionchange', rememberSelection);
editor.addEventListener('input', () => { dirty = true; visualMarkdown = null; });
source.addEventListener('input', () => {
    dirty = true; ++previewVersion; clearTimeout(previewTimer);
    previewTimer = setTimeout(updatePreview, 250);
});
document.querySelectorAll('[data-command]').forEach(button => {
    button.addEventListener('mousedown', event => event.preventDefault());
    button.addEventListener('click', () => {
        editor.focus();
        if (selectionRange) {
            const selection = window.getSelection();
            selection.removeAllRanges(); selection.addRange(selectionRange);
        }
        document.execCommand(button.dataset.command, false, button.dataset.value || null);
        dirty = true; visualMarkdown = null;
    });
});
editor.addEventListener('paste', event => {
    event.preventDefault();
    document.execCommand('insertText', false, event.clipboardData.getData('text/plain'));
    dirty = true; visualMarkdown = null;
});
document.getElementById('load-example').addEventListener('click', () => {
    if ((mode === 'markdown' ? source.value.trim() : editor.textContent.trim()) && !window.confirm(isGerman ? 'Aktuellen Entwurf durch das Beispiel ersetzen?' : 'Replace the current draft with the example?')) return;
    editor.innerHTML = document.getElementById('notice-example').innerHTML;
    visualMarkdown = null;
    if (mode === 'markdown') {
        source.value = Array.from(editor.childNodes).map(markdownText).join('').trim(); updatePreview(); source.focus();
    } else editor.focus();
    selectionRange = null; dirty = true;
});
form.addEventListener('submit', () => {
    const preserveMarkdown = mode === 'html' && visualMarkdown !== null;
    document.getElementById('notice-content').value = mode === 'markdown' ? source.value : (preserveMarkdown ? visualMarkdown : editor.innerHTML);
    document.getElementById('notice-format').value = preserveMarkdown ? 'markdown' : mode;
    dirty = false;
});
window.addEventListener('beforeunload', event => {
    if (dirty) { event.preventDefault(); event.returnValue = ''; }
});
updateMode();
