#!/bin/bash
echo "Pushing to github with comment:" \"$@\"
git add ./*.py ./*.sh ./logsim/*.py
if [ $# -gt 0 ]
then
	git commit -m \"$@\"
else
	git commit -m \"Update\"
fi
git push