const https = require('https');

function fetchPage(url) {
  return new Promise((resolve, reject) => {
    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'identity',
        'Cache-Control': 'no-cache'
      }
    };
    https.get(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

function extractBatting(html) {
  const batters = [];
  // Cricbuzz scorecard batting rows
  const battingRegex = /<a[^>]*href="[^"]*\/profiles\/\d+\/[^"]*"[^>]*>([^<]+)<\/a>[\s\S]*?<\/td>[\s\S]*?<td[^>]*>(\d+)<\/td>[\s\S]*?<td[^>]*>(\d+)<\/td>/g;
  let m;
  while ((m = battingRegex.exec(html)) !== null) {
    const name = m[1].trim();
    const runs = parseInt(m[2]);
    const balls = parseInt(m[3]);
    if (name && !isNaN(runs)) {
      batters.push({ name, runs, balls });
    }
  }
  return batters;
}

function extractBowling(html) {
  const bowlers = [];
  // Extract bowling figures: name, overs, maidens, runs, wickets
  const bowlingSection = html.match(/bowling[\s\S]*?(?=<\/table>)/gi);
  if (bowlingSection) {
    const rowRegex = /<a[^>]*href="[^"]*\/profiles\/\d+\/[^"]*"[^>]*>([^<]+)<\/a>[\s\S]*?<td[^>]*>([\d.]+)<\/td>[\s\S]*?<td[^>]*>(\d+)<\/td>[\s\S]*?<td[^>]*>(\d+)<\/td>[\s\S]*?<td[^>]*>(\d+)<\/td>/g;
    bowlingSection.forEach(section => {
      let m;
      while ((m = rowRegex.exec(section)) !== null) {
        bowlers.push({
          name: m[1].trim(),
          overs: m[2],
          maidens: parseInt(m[3]),
          runs: parseInt(m[4]),
          wickets: parseInt(m[5])
        });
      }
    });
  }
  return bowlers;
}

// Better approach: use Cricbuzz's own JSON endpoints
async function getCricbuzzData(matchId) {
  try {
    const url = `https://www.cricbuzz.com/api/cricket-scorecard/${matchId}`;
    const html = await fetchPage(url);
    const data = JSON.parse(html);
    return { source: 'json', data };
  } catch(e) {
    // fallback to scraping
    const url = `https://www.cricbuzz.com/live-cricket-scorecard/${matchId}`;
    const html = await fetchPage(url);
    return { source: 'html', html };
  }
}

module.exports = async (req, res) => {
  const matchId = req.query.id;
  
  if (!matchId) {
    return res.status(400).json({ error: 'Match ID required. Use ?id=<cricbuzz_match_id>' });
  }

  try {
    // Try Cricbuzz's internal API first
    const url = `https://www.cricbuzz.com/api/cricket-scorecard/${matchId}`;
    const raw = await fetchPage(url);
    
    let scorecard;
    try {
      scorecard = JSON.parse(raw);
    } catch(e) {
      return res.status(500).json({ error: 'Could not parse scorecard', raw: raw.substring(0, 500) });
    }

    // Extract batting and bowling from all innings
    const result = { matchId, innings: [] };
    
    const inningsList = scorecard.scoreCard || scorecard.innings || [];
    inningsList.forEach((inn, idx) => {
      const inning = {
        team: inn.batTeamDetails?.batTeamName || `Innings ${idx + 1}`,
        score: `${inn.scoreDetails?.runs || 0}/${inn.scoreDetails?.wickets || 0}`,
        overs: inn.scoreDetails?.overs || 0,
        batting: [],
        bowling: []
      };

      // Batting
      const batsmen = inn.batTeamDetails?.batsmenData || {};
      Object.values(batsmen).forEach(b => {
        if (b.batName && b.runs !== undefined) {
          inning.batting.push({
            name: b.batName,
            runs: b.runs,
            balls: b.balls,
            fours: b.fours,
            sixes: b.sixes,
            strikeRate: b.strikeRate,
            dismissal: b.outDesc || 'not out'
          });
        }
      });

      // Bowling
      const bowlers = inn.bowlTeamDetails?.bowlersData || {};
      Object.values(bowlers).forEach(b => {
        if (b.bowlName && b.wickets !== undefined) {
          inning.bowling.push({
            name: b.bowlName,
            overs: b.overs,
            maidens: b.maidens,
            runs: b.runs,
            wickets: b.wickets,
            economy: b.economy
          });
        }
      });

      result.innings.push(inning);
    });

    res.setHeader('Access-Control-Allow-Origin', '*');
    res.json({ status: 'success', ...result });

  } catch(err) {
    res.status(500).json({ error: err.message });
  }
};
