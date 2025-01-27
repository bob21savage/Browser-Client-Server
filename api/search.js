const { exec } = require('child_process');

export default function handler(req, res) {
    if (req.method === 'POST') {
        const { query } = req.body;

        // Run your Python script with the query
        exec(`python ./scrape/scrape_upgrade.py ${query}`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error executing script: ${error}`);
                return res.status(500).json({ error: 'Internal Server Error' });
            }
            res.status(200).json({ output: stdout });
        });
    } else {
        res.setHeader('Allow', ['POST']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
