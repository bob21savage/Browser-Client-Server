const { exec } = require('child_process');

export default function handler(req, res) {
    if (req.method === 'POST') {
        const { query } = req.body;

        // Run your Python script with the query
        exec(`python ./app.py ${query}`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error executing script: ${error.message}`);
                return res.status(500).json({ error: 'Internal Server Error', message: error.message });
            }
            if (stderr) {
                console.error(`stderr: ${stderr}`);
                return res.status(500).json({ error: 'Script Error', message: stderr });
            }
            res.status(200).json({ output: stdout });
        });
    } else {
        res.setHeader('Allow', ['POST']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
