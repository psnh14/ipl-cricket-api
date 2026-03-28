const https = require('https');

function fetchPage(url) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/html',
      }
    };
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

module.exports = async (req, res) => {
  try {
    const raw = await fetchPage('https://www.cricbuzz.com/api/cricket-match/live');
    const data = JSON.parse(raw);
    
    const matches = [];
    const types = data.typeMatches || [];
    types.forEach(type => {
      (type.seriesMatches || []).forEach(sm => {
        const series = sm.seriesAdWrapper || sm;
        (series.matches || []).forEach(m => {
          const mi = m.matchInfo || m;
          matches.push({
            id: mi.matchId || mi.id,
            title: `${mi.team1?.teamSName || ''} vs ${mi.team2?.teamSName || ''}`,
            series: series.seriesName || '',
            state: mi.state || mi.matchFormat,
            status: mi.status
          });
        });
      });
    });

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.json({ status: 'success', count: matches.length, matches });
  } catch(err) {
    res.status(500).json({ error: err.message });
  }
};
