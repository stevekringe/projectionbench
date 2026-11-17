const names: Record<string, string> = {
	'cloudflare:@cf/qwen/qwen3.8-27b@cloudflare': 'Qwen 3.8 27B',
	'cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low': 'Qwen 3.8 27B (low reasoning)',
	'cloudflare:@cf/meta/llama-3.3-70b-instruct-fp8-fast@cloudflare': 'Llama 3.3 70B'
};

export function matchedModelName(subject: string) {
	return names[subject] ?? subject.replace(/^gemini:gemini-/, 'Gemini ')
		.replace(/-flash-lite(?=@api$)/, ' Flash-Lite')
		.replace(/-flash(?=@api$)/, ' Flash')
		.replace(/@api$/, '');
}
