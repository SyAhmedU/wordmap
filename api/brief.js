const Anthropic = require('@anthropic-ai/sdk');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { term, group, share, growth, novelty, count, peakYear } = req.body || {};
  if (!term) return res.status(400).json({ error: 'Missing term' });

  const client = new Anthropic.default();

  const prompt = `You are a research strategy advisor for social scientists. Analyse this bibliometric data and write a concise research opportunity brief.

Term: "${term}" (subfield: ${group})
Doc-frequency share: ${share}% of all social science papers
5-year growth rate: ${growth}%/yr
Novelty (concentration in last 5 years): ${novelty}%
Papers in current year: ${Number(count).toLocaleString()}
Peak publication year: ${peakYear}

Write exactly 3 short paragraphs (150 words total maximum):
1. Why this term is moving NOW — name the specific real-world drivers, key papers, or intellectual shifts causing the trend
2. The most promising underexplored angle for a researcher entering this space today
3. One specific, defensible research question suitable for a PhD thesis or competitive grant proposal

Be concrete. Name actual theories, methods, or empirical contexts. No generic advice. Write for a senior researcher.`;

  try {
    const message = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 600,
      messages: [{ role: 'user', content: prompt }]
    });
    res.json({ brief: message.content[0].text });
  } catch (err) {
    res.status(500).json({ error: 'Claude API error: ' + err.message });
  }
};
