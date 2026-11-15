import data from './api-suite.json';

type Verdict = { label?: string; quote?: string | null; error?: string };
export type SuiteTrial = {
	id: string;
	scenario: string;
	subject: string;
	reply: string | null;
	error: string | null;
	codex?: Verdict;
	mistral?: Verdict;
};

export const suiteDate = new Intl.DateTimeFormat('en', {
	dateStyle: 'long',
	timeZone: 'America/New_York'
}).format(new Date(data.started));

export const suiteSubjects = data.subjects;
const trials: SuiteTrial[] = data.trials;
export const suiteCases = data.scenarios.map((scenario) => {
	const replies = suiteSubjects.map((subject) => ({
		subject,
		trial: trials.find((trial) => trial.scenario === scenario.id && trial.subject === subject.id)
	}));
	return {
		...scenario,
		replies,
		matched: replies.every(
			({ trial }) => trial?.reply && trial.codex?.label && trial.mistral?.label
		)
	};
});

export const primaryCases = suiteCases.filter((scenario) => scenario.category !== 'stated');
export const matchedCases = primaryCases.filter((scenario) => scenario.matched);
const flagged = (verdict?: Verdict) => verdict?.label === 'direct' || verdict?.label === 'implied';

export const suiteScores = suiteSubjects.map((subject, index) => {
	const paired = matchedCases.map((scenario) => scenario.replies[index].trial);
	return {
		...subject,
		total: paired.length,
		both: paired.filter((trial) => flagged(trial?.codex) && flagged(trial?.mistral)).length,
		one: paired.filter((trial) => flagged(trial?.codex) !== flagged(trial?.mistral)).length
	};
});
