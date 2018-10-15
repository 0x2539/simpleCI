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

curl -X POST \
  https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
  -H "Authorization: token ${gitToken}" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "pending",
  "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
  "description": "Health checks pending",
  "context": "continuous-integration/health_checks"
}'

curl -X POST \
  https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
  -H "Authorization: token ${gitToken}" \
  -H 'Cache-Control: no-cache' \
  -H 'Content-Type: application/json' \
  -d '{
  "state": "pending",
  "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
  "description": "Test execution pending",
  "context": "continuous-integration/tests_appium_selenium"
}'

repoFolder="${HOME}/builds/cex-${gitCommit}"
frontRepoFolder="${HOME}/builds/cex-${gitCommit}/src/crypto-frontend"

rm -rf ${repoFolder}
mkdir -p ${repoFolder}
echo "git clone https://${gitToken}@github.com/${REPO_PATH} ${repoFolder}"
git clone https://${gitToken}@github.com/${REPO_PATH} ${repoFolder}
echo "cd ${repoFolder}"
cd ${repoFolder}
echo "git checkout ${gitCommit}"
git checkout ${gitCommit}

rm -rf ${frontRepoFolder}
mkdir -p ${frontRepoFolder}
echo "git clone https://gitlab.com/${FRONT_REPO_PATH} --branch appium_selenium_integration --single-branch ${frontRepoFolder}"
git clone https://gitlab.com/${FRONT_REPO_PATH} --branch appium_selenium_integration --single-branch ${frontRepoFolder}
echo "cd ${frontRepoFolder}"
cd ${frontRepoFolder}
echo "git checkout appium_selenium_integration"
git checkout appium_selenium_integration

touch ${HOME}/buildMessages/${gitCommit}/log.txt
set +e

echo "python3 ${repoFolder}/src/buildScripts/run_integration_tests.py ${gitCommit} devclient dev > ${HOME}/buildMessages/${gitCommit}/log.txt"
python3 ${repoFolder}/src/buildScripts/run_integration_tests.py ${gitCommit} devclient dev > ${HOME}/buildMessages/${gitCommit}/log.txt;
status=$?

if [ $status -eq 1 ]; then
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

    curl -X POST \
      https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
      -H "Authorization: token ${gitToken}" \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{
      "state": "error",
      "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
      "description": "Health checks failed",
      "context": "continuous-integration/health_checks"
    }'

    curl -X POST \
      https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
      -H "Authorization: token ${gitToken}" \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{
      "state": "error",
      "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
      "description": "Integration tests failed",
      "context": "continuous-integration/tests_appium_selenium"
    }'
elif [ $status -eq 2 ]; then
    if [ -f "${repoFolder}/src/buildScripts/error_file" ]; then
        foo=$(cat ${repoFolder}/src/buildScripts/error_file | tr -dc '[:alnum:]:,')
        echo "${repoFolder}/src/buildScripts/error_file ${HOME}/buildMessages/${gitCommit}"
        cp ${repoFolder}/src/buildScripts/error_file ${HOME}/buildMessages/${gitCommit}

        curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Build successful",
          "context": "continuous-integration/ce"
        }'
        curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "error",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": '${foo}',
          "context": "continuous-integration/health_checks"
        }'

        curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "error",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Integration tests failed",
          "context": "continuous-integration/tests_appium_selenium"
        }'
    fi
elif [ $status -eq 3 ]; then
    curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Build successful",
          "context": "continuous-integration/ce"
        }'
    curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Health checks passed",
          "context": "continuous-integration/health_checks"
        }'
    curl -X POST \
      https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
      -H "Authorization: token ${gitToken}" \
      -H 'Cache-Control: no-cache' \
      -H 'Content-Type: application/json' \
      -d '{
      "state": "error",
      "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
      "description": "Integration tests failed",
      "context": "continuous-integration/tests_appium_selenium"
    }'
elif [ $status -eq 0 ]; then
    curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Build successful",
          "context": "continuous-integration/ce"
        }'
    curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Health checks passed",
          "context": "continuous-integration/health_checks"
        }'
    curl -X POST \
          https://api.github.com/repos/${REPO_PATH}/statuses/${gitCommit} \
          -H "Authorization: token ${gitToken}" \
          -H 'Cache-Control: no-cache' \
          -H 'Content-Type: application/json' \
          -d '{
          "state": "success",
          "target_url": "'${CI_URL}'/buildMessages/'${gitCommit}'.txt",
          "description": "Integration tests passed",
          "context": "continuous-integration/tests_appium_selenium"
        }'

    echo "cp -r ${repoFolder}/src/buildScripts/screenshots ${HOME}/buildMessages/${gitCommit}"
    cp -r ${repoFolder}/src/buildScripts/screenshots ${HOME}/buildMessages/${gitCommit}
fi

echo "rm -rf ${repoFolder}"
rm -rf ${repoFolder}

echo "ended at $(dateString) ($(timestamp)) (duration: $(($(timestamp)-${startTs})) seconds)"
