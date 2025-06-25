<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Python Project Setup</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      margin: 2em;
      background-color: #f5f5f5;
      color: #333;
    }
    h1 {
      color: #2c3e50;
    }
    code {
      background-color: #eaeaea;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
    }
    pre {
      background-color: #eee;
      padding: 10px;
      border-left: 5px solid #ccc;
      overflow-x: auto;
    }
    section {
      margin-bottom: 2em;
    }
  </style>
</head>
<body>
  <h1>Python Project Setup</h1>

  <section>
    <h2>1. Create and Activate a Virtual Environment (Linux)</h2>
    <pre><code>python3 -m venv venv
source venv/bin/activate</code></pre>
    <p>This creates an isolated environment for your Python dependencies.</p>
  </section>

  <section>
    <h2>2. Export API Keys as Environment Variables</h2>
    <p>Replace the placeholders with your actual API keys:</p>
    <pre><code>export TAVILY_API_KEY="your_tavily_api_key"
export NVIDIA_API_MISTRAL_MEDIUM3_INSTRUCT="your_nvidia_api_key"</code></pre>
    <p>To make these persist, you can add them to your <code>~/.bashrc</code> or <code>~/.zshrc</code> file.</p>
  </section>

  <section>
    <h2>3. Install Dependencies</h2>
    <p>Make sure you're in your virtual environment, then run:</p>
    <pre><code>pip install -r requirements.txt</code></pre>
    <p>This installs all required packages listed in <code>requirements.txt</code>.</p>
  </section>

  <section>
    <h2>4. Run the Project</h2>
    <p>After setup, you can run your Python scripts as usual:</p>
    <pre><code>python main.py</code></pre>
  </section>

  <footer>
    <p><em>Make sure to keep your API keys secret and never commit them to version control!</em></p>
  </footer>
</body>
</html>
