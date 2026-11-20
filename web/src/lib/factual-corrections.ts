import study from './factual-corrections.json';

const scenarios = new Map(study.scenarios.map((scenario) => [scenario.id, scenario]));
const total = study.scenarios.length * study.samples;
const isFlag = (label: string | undefined) => label === 'direct' || label === 'implied';

export const correctionStudy = study;
export const correctionModels = study.subjects.map((subject) => {
	const trials = study.trials.filter((trial) => trial.subject === subject.id);
	const reviewed = trials.filter((trial) => trial.reference);
	const complete = study.scenarios.every(({ id }) =>
		Array.from({ length: study.samples }, (_, index) => index + 1).every((sample) =>
			reviewed.some((trial) => trial.scenario === id && trial.sample === sample)
		)
	);
	const flagged = reviewed.filter((trial) => isFlag(trial.reference?.label)).length;
	const paired = reviewed.filter((trial) => trial.secondReview?.label);
	const disagreements = paired.filter((trial) =>
		isFlag(trial.reference?.label) !== isFlag(trial.secondReview?.label)
	).length;
	const phases = (['first', 'repeat'] as const).map((phase) => {
		const rows = reviewed.filter((trial) => trial.scenario.endsWith(`_${phase}`));
		const example = rows.find((trial) => isFlag(trial.reference?.label))
			?? rows.find((trial) => trial.reference?.label === 'uncertain')
			?? rows[0];
		return {
			label: phase === 'first' ? 'First correction' : 'After a repeated error',
			flagged: rows.filter((trial) => isFlag(trial.reference?.label)).length,
			eligible: rows.length,
			example: example?.reply ? {
				title: scenarios.get(example.scenario)?.title ?? '',
				history: scenarios.get(example.scenario)?.messages ?? [],
				excerpt: example.reference?.quote ?? example.reply.trim().split(/\n\s*\n/, 1)[0],
				flagged: isFlag(example.reference?.label),
				uncertain: example.reference?.label === 'uncertain',
				reply: example.reply
			} : null
		};
	});
	return {
		...subject, subject: subject.id, planned: total, eligible: reviewed.length,
		value: complete ? 100 * flagged / total : null,
		flagged, phases, disagreements, paired: paired.length,
		uncertain: reviewed.filter((trial) => trial.reference?.label === 'uncertain').length
	};
});
