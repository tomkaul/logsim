#!/bin/bash
echo "Pushing to github with comment:" \"$@\"
echo git add ./*.py ./*.sh ./logsim/*.py
git add ./*.py ./*.sh ./logsim/*.py
if [ $# -gt 0 ]
then
	echo git commit -m \"$@\"
	git commit -m \"$@\"
else
	echo git commit -m \"Update\"
	git commit -m \"Update\"
fi
echo git push
git push
