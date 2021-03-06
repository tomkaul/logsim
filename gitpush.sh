#!/bin/bash
echo "Pushing to github with comment:" \"$@\"
git add ./*.py ./*.sh ./logsim/*.py ./*.ipynb ./*.txt

MSG="Update"
if [ $# -gt 0 ]
then
    MSG="$@"
fi
git commit -m "$MSG"
git push
