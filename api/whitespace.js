const Anthropic = require('@anthropic-ai/sdk');

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { term1, group1, growth1, term2, group2, growth2 } = req.body || {};
  if (!term1 || !term2) return res.status(400).json({ error: 'Missing terms' });

  const client = new Anthropic.default();

  const prompt = `You are a research strategist specialising in social science. Two research areas are both growing in the literature:

1. "${term1}" (${group1}, ${growth1}%/yr growth)
2. "${term2}" (${group2}, ${growth2}%/yr growth)

Identify the white space at their intersection. Write exactly 3 short paragraphs (150 words total maximum):
1. What research sits at the intersection of these two areas that is currently understudied — be specific about what is MISSING, not what exists
2. Why this intersection is now timely and tractable — name the methodological tools, datasets, or theoretical frameworks that make it feasible today
3. One concrete research question that would establish genuinely new ground at this intersection, suitable for a high-impact journal or major grant

Name actual theories, empirical contexts, and methods. Avoid generalities. Write for a senior researcher planning their next project.`;

  try {
    const message = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 600,
      messages: [{ role: 'user', content: prompt }]
    });
    res.json({ analysis: message.content[0].text });
  } catch (err) {
    res.status(500).json({ error: 'Claude API error: ' + err.message });
  }
};
