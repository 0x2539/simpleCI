#!/bin/bash

set -e

# Define a timestamp function
timestamp() {
  date +"%s"
}

dateString() {
  date +"%T"
}

startTs=$(timestamp)
echo "started at $(dateString) ($(timestamp))"

for i in "$@"
do
case $i in
    --gitCommit=*)
    gitCommit="${i#*=}"
    ;;
    --pullRequestNumber=*)
    pullRequestNumber="${i#*=}"
    ;;
    --gitToken=*)
    gitToken="${i#*=}"
    ;;
    *)
    echo "unknown option ${i}"
    echo "ended at $(dateString) ($(timestamp)) (duration: $(($(timestamp)-${startTs})) seconds)"
    exit -1
    ;;
esac
done

if [[ -z "${gitToken}" ]]; then
echo "git access token is missing, set it as environment variable or pass it as argument ('./run_tests.sh --gitToken=123' or 'export gitToken=123')"
echo "ended at $(dateString) ($(timestamp)) (duration: $(($(timestamp)-${startTs})) seconds)"
exit -1
fi

if [[ -z "${CI_URL}" ]]; then
echo "CI_URL enironment variable is missing (set it to something like: https://ci.myapp.com). This will be used to view the output from tests"
echo "ended at $(dateString) ($(timestamp)) (duration: $(($(timestamp)-${startTs})) seconds)"
exit -1
fi

curl -X POST \
  https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
  -H "Authorization: token ${gitToken}" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "pending",
  "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
  "description": "Build pending",
  "context": "continuous-integration/ce"
}'

repoFolder="${HOME}/builds/cex-${gitCommit}"
rm -rf ${repoFolder}
mkdir -p ${repoFolder}


echo "git clone https://${gitToken}@github.com/${REPO_PATH} ${repoFolder}"
git clone https://${gitToken}@github.com/${REPO_PATH} ${repoFolder}

echo "cd ${repoFolder}"
cd ${repoFolder}

echo "git checkout ${gitCommit}"
git checkout ${gitCommit}


echo "python3 ${repoFolder}/src/buildScripts/run_tests.py > ${HOME}/buildMessages/${gitCommit}.txt"
if ! python3 ${repoFolder}/src/buildScripts/run_tests.py > ${HOME}/buildMessages/${gitCommit}.txt & echo $! > ${HOME}/buildMessages/${gitCommit}-pid.txt ; then

curl -X POST \
  https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
  -H "Authorization: token ${gitToken}" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "error",
  "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
  "description": "Build failed",
  "context": "continuous-integration/ce"
}'

else

curl -X POST \
  https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
  -H "Authorization: token ${gitToken}" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "success",
  "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
  "description": "Build success",
  "context": "continuous-integration/ce"
}'

fi

rm -rf ${repoFolder}

echo "ended at $(dateString) ($(timestamp)) (duration: $(($(timestamp)-${startTs})) seconds)"
