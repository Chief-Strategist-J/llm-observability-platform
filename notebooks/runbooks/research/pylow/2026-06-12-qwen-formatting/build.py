#!/usr/bin/env python3
import os
import sys
import subprocess
import glob

def compile_pdf(tex_filename, runs=2):
    if not os.path.exists(tex_filename):
        print(f"Error: File '{tex_filename}' not found!")
        return False

    base_name = os.path.splitext(os.path.basename(tex_filename))[0]
    cwd = os.getcwd()

    # Define files we want to keep
    # We only want to keep the .tex and the generated .pdf
    keep_extensions = {'.tex', '.pdf'}

    print(f"Compiling {tex_filename} using blang/latex docker container (runs={runs})...")
    
    # Run pdflatex using Docker
    for i in range(1, runs + 1):
        print(f"--- Pass {i} ---")
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{cwd}:/data",
            "-w", "/data",
            "blang/latex",
            "pdflatex", tex_filename
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Compilation failed! LaTeX log output:")
            print(result.stdout)
            print(result.stderr)
            return False
        print("Pass successful.")

    print("\nCleaning up auxiliary files...")
    # List of extensions typically created during pdflatex compilation
    aux_extensions = ['.aux', '.log', '.out', '.toc', '.synctex.gz', '.fls', '.fdb_latexmk', '.nav', '.snm', '.vrb']
    
    deleted_files = []
    for ext in aux_extensions:
        pattern = os.path.join(cwd, f"*{ext}")
        for filepath in glob.glob(pattern):
            try:
                os.remove(filepath)
                deleted_files.append(os.path.basename(filepath))
            except Exception as e:
                print(f"Failed to remove {filepath}: {e}")

    if deleted_files:
        print(f"Successfully cleaned up: {', '.join(deleted_files)}")
    else:
        print("No auxiliary files to clean up.")
        
    print(f"\nDone! Only '{base_name}.tex' and '{base_name}.pdf' are preserved.")
    return True

if __name__ == "__main__":
    # If a file is passed as an argument, compile it; otherwise compile peft_lora.tex
    filename = sys.argv[1] if len(sys.argv) > 1 else "peft_lora.tex"
    success = compile_pdf(filename)
    sys.exit(0 if success else 1)
