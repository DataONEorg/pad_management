#!flask/bin/python
import os

extra_dirs = ['./app/templates', ]
extra_files = extra_dirs[:]
for extra_dir in extra_dirs:
  for dirname, dirs, files in os.walk(extra_dir):
    for filename in files:
      filename = os.path.join(dirname, filename)
      if os.path.isfile(filename):
        extra_files.append(filename)

from app import app
app.run(debug=True, extra_files=extra_files)

