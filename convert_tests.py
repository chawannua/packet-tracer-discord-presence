import os
import glob
import re

for file in glob.glob("tests/test_*.py"):
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check if already has unittest.TestCase
    if "class Test" in content:
        continue
        
    # Replace simple functions with methods in a TestCase class
    # Add import unittest
    if "import unittest" not in content:
        content = "import unittest\n" + content
    
    # replace 'import pytest' with ''
    content = content.replace("import pytest\n", "")
    
    # Change 'def test_*(...):' to 'class Test*(unittest.TestCase):'
    # Wait, we should group all def test_* into one class TestSomething(unittest.TestCase):
    
    # Let's extract all imports and globals, and then functions
    lines = content.split('\n')
    new_lines = []
    class_started = False
    class_name = "Test" + os.path.basename(file).replace("test_", "").replace(".py", "").title()
    
    for line in lines:
        if line.startswith("def test_"):
            if not class_started:
                new_lines.append(f"\nclass {class_name}(unittest.TestCase):")
                class_started = True
            
            # modify signature to include self
            # check if it has args
            if line.endswith("():"):
                new_lines.append("    " + line.replace("():", "(self):"))
            else:
                new_lines.append("    " + line.replace("(", "(self, "))
        elif class_started and (line.startswith("    ") or line == ""):
            # indent it more
            if line == "":
                new_lines.append("")
            else:
                # also replace asserts
                new_line = "    " + line
                # naive assert replacement
                if new_line.strip().startswith("assert "):
                    cond = new_line.strip()[7:]
                    if " == " in cond:
                        parts = cond.split(" == ")
                        new_line = new_line.replace(f"assert {cond}", f"self.assertEqual({parts[0]}, {parts[1]})")
                    elif " is " in cond:
                        parts = cond.split(" is ")
                        new_line = new_line.replace(f"assert {cond}", f"self.assertIs({parts[0]}, {parts[1]})")
                    else:
                        new_line = new_line.replace(f"assert {cond}", f"self.assertTrue({cond})")
                new_lines.append(new_line)
        else:
            if not line.startswith("def test_") and class_started:
                # end of class methods?
                pass
            new_lines.append(line)
            
    with open(file, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))
