const express = require('express');
const fs = require('fs');
const app = express();

app.use(express.json());

// Allow CORS so frontend can POST
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

app.post('/save', (req, res) => {
  fs.writeFile('with_aime_answers.json', JSON.stringify(req.body, null, 2), err => {
    if (err) {
      console.error(err);
      return res.status(500).send('Failed to save');
    }
    res.send('Saved!');
  });
});

app.listen(3001, () => console.log('Backend server running on http://localhost:3001'));
