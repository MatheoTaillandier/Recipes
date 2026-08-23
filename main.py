import subprocess

if __name__ == "__main__":
    subprocess.run(["uv", "run", "streamlit", "run", "src/app.py"], check=False)