#!/bin/bash
echo "Pushing to github with comment:" \"$@\"
echo git add ./*.py ./*.sh ./logsim/*.py
git add ./*.py ./*.sh ./logsim/*.py
MSG="Update"
if [ $# -gt 0 ]
then
    MSG="$@"
fi
echo git commit -m "$MSG"
git commit -m "$MSG"
echo git push
git push
