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
            console.log(`Raw output from Python script: ${stdout}`); // Log the raw output for debugging
            try {
                const output = JSON.parse(stdout); // Try to parse the output as JSON
                res.status(200).json(output);
            } catch (parseError) {
                console.error(`Output parsing error: ${parseError.message}`);
                console.error(`Raw output: ${stdout}`); // Log the raw output for debugging
                res.status(500).json({ error: 'Output Parsing Error', message: stdout }); // Return the raw output if parsing fails
            }
        });
    } else {
        res.setHeader('Allow', ['POST']);
        res.status(405).end(`Method ${req.method} Not Allowed`);
    }
}
