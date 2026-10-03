const normalise = value => value.normalize('NFKC').toLocaleLowerCase().trim();
for (const input of document.querySelectorAll('[data-filter]')) {
    const items = Array.from(document.querySelectorAll(input.dataset.filter));
    const empty = Array.from(document.querySelectorAll('[data-filter-empty]')).find(node => node.dataset.filterEmpty === input.dataset.filter);
    input.addEventListener('input', () => {
        const query = normalise(input.value);
        let matches = 0;
        for (const item of items) {
            item.hidden = !normalise(item.dataset.search || item.textContent).includes(query);
            if (!item.hidden) matches += 1;
        }
        if (empty) empty.hidden = matches !== 0;
    });
}
for (const input of document.querySelectorAll('[data-member-search]')) {
    const select = document.getElementById(input.dataset.memberSearch);
    const options = Array.from(select.options).map(option => option.cloneNode(true));
    const submit = select.form.querySelector('button[type="submit"],button:not([type])');
    input.addEventListener('input', () => {
        const selected = select.value;
        const matches = options.filter(option => normalise(option.textContent).includes(normalise(input.value)));
        select.replaceChildren(...matches.map(option => option.cloneNode(true)));
        if (matches.some(option => option.value === selected)) select.value = selected;
        select.disabled = matches.length === 0;
        if (submit) submit.disabled = matches.length === 0;
    });
}
for (const button of document.querySelectorAll('[data-step]')) {
    button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.target);
        if (!input.value || !input.validity.valid) input.value = input.min || '1';
        if (Number(button.dataset.step) > 0) input.stepUp(); else input.stepDown();
        input.dispatchEvent(new Event('input', {bubbles: true}));
    });
}
for (const button of document.querySelectorAll('[data-fill]')) {
    button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.target);
        input.value = button.dataset.fill;
        input.dispatchEvent(new Event('input', {bubbles: true}));
    });
}
for (const button of document.querySelectorAll('[data-partial]')) {
    button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.partial);
        input.value = ''; input.focus();
    });
}
for (const form of document.querySelectorAll('form[method="post"]')) {
    form.addEventListener('submit', event => {
        if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
        if (event.defaultPrevented) return;
        const submitter = event.submitter;
        // Disabled buttons do not submit their name/value. Preserve the tapped product.
        if (submitter && submitter.name) {
            const input = document.createElement('input');
            input.type = 'hidden'; input.name = submitter.name; input.value = submitter.value;
            input.dataset.submitValue = 'true'; form.appendChild(input);
        }
        form.dataset.submitting = 'true'; form.setAttribute('aria-busy', 'true');
        if (submitter) {
            submitter.dataset.originalHtml = submitter.innerHTML;
            submitter.disabled = true;
            submitter.textContent = form.dataset.pendingLabel || document.body.dataset.pendingLabel;
        }
        const status = document.getElementById('submission-status');
        if (status) status.textContent = form.dataset.pendingLabel || document.body.dataset.pendingLabel;
    });
}
window.addEventListener('pageshow', () => {
    for (const form of document.querySelectorAll('form[data-submitting]')) {
        delete form.dataset.submitting; form.removeAttribute('aria-busy');
        for (const button of form.querySelectorAll('[data-original-html]')) {
            button.innerHTML = button.dataset.originalHtml; button.disabled = false;
            delete button.dataset.originalHtml;
        }
        for (const input of form.querySelectorAll('[data-submit-value]')) input.remove();
    }
});
