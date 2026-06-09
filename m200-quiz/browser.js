const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

async function getQuizQuestions(part) {
    const result = await fetch(`/quiz.php?part=${part}`, { cache: 'no-store' });
    if (result.status == 200) {
        const match = (await result.text()).match(/const currentQuestions = (\[[\s\S]*?\]);/);
        if (match) {
            return JSON.parse(match[1]);
        }
    }
    return [];
}

async function getAllQuizQuestions(part) {
    const seen = new Map();
    let consecutiveEmpty = 0;
    while (consecutiveEmpty < 5) {
        console.log(`Fetching (${consecutiveEmpty})`);
        const questions = await getQuizQuestions(part);

        let haveNew = false;
        for (const question of questions) {
            if (!seen.has(question.question)) {
                seen.set(question.question, question);
                haveNew = true;
            }
        }

        consecutiveEmpty = haveNew ? 0 : consecutiveEmpty + 1;
        await sleep(1000);
    }
    return [...seen.values()];
}

async function downloadAllQuizQuestions(part) {
    const questions = await getAllQuizQuestions(part);

    const json = JSON.stringify(questions, null, 2);
    const blob = new Blob([json], { type: 'application/json' });

    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `m200-quiz-${part}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
}
