const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function getCourseSessionIds(courseId) {
    const sessions = new Map();
    const result = await fetch(`/app/course/${courseId}/`);
    if (result.status == 200) {
        const doc = (new DOMParser()).parseFromString(await result.text(), 'text/html');
        doc.querySelectorAll('.col-session').forEach(card => {
            const href = card.querySelector('a[href*="/session/"]')?.getAttribute('href');
            const name = card.querySelector('.session-card-detail')?.getAttribute('title');
            if (href && name) {
                const id = href.split('/session/')[1];
                sessions.set(id, name);
            }
        });
    }
    return sessions;
}

async function getSessionDocumentIds(courseId, sessionId) {
    const documents = new Map();
    const result = await fetch(`/app/course/${courseId}/session/${sessionId}/docs`);
    if (result.status == 200) {
        const doc = (new DOMParser()).parseFromString(await result.text(), 'text/html');
        doc.querySelectorAll('a.btn-primary').forEach(a => {
            const href = a.getAttribute('href');
            if (href && href.includes('/docs/')) {
                const id = href.split('/docs/')[1];
                const name = a.closest('.panel')?.querySelector('.panel-heading b')?.textContent?.trim();
                documents.set(id, `${name}.pdf`);
            }
        });
    }
    return documents;
}

async function getDocumentUrl(courseId, sessionId, documentId) {
    const result = await fetch(`/app/course/${courseId}/session/${sessionId}/docs/${documentId}`);
    if (result.status == 200) {
        const doc = (new DOMParser()).parseFromString(await result.text(), 'text/html');
        const link = doc.querySelector('a.btn-info[download]');
        if (link) {
            return link.getAttribute('href');
        }
    }
    return null;
}

async function downloadDocument(sessionName, documentName, url) {
    const fileName = `Fred~~M200~~${btoa(`${sessionName}/${documentName}`)}`;
    console.log(fileName);
    const result = await fetch(url);
    if (result.status == 200) {
        const blob = await result.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(a.href);
    }
}

async function downloadAllCourseFiles(courseId) {
    const courseSessionIds = await getCourseSessionIds(courseId);
    for (const [sessionId, sessionName] of courseSessionIds) {
        const sessionDocumentIds = await getSessionDocumentIds(courseId, sessionId);
        for (const [documentId, documentName] of sessionDocumentIds) {
            const downloadUrl = await getDocumentUrl(courseId, sessionId, documentId);
            if (downloadUrl) {
                await downloadDocument(sessionName, documentName, downloadUrl);
                await sleep(1000);
            }
        }
        await sleep(1000);
    }
}
